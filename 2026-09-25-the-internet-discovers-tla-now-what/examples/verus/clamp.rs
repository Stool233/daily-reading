use vstd::prelude::*;

verus! {

// Mathematical definition: unbounded integers, no runtime execution.
spec fn clamp_spec(x: int, lo: int, hi: int) -> int {
    if x < lo { lo } else if x > hi { hi } else { x }
}

// The empty body is checked by the SMT solver; this is not an assumption.
proof fn lemma_clamp_bounds(x: int, lo: int, hi: int)
    requires lo <= hi,
    ensures lo <= clamp_spec(x, lo, hi) <= hi,
{
}

// Default mode is exec: this body becomes ordinary machine code.
fn clamp_value(x: u32, lo: u32, hi: u32) -> (r: u32)
    requires lo <= hi,
    ensures
        r as int == clamp_spec(x as int, lo as int, hi as int),
        lo <= r <= hi,
{
    let r = if x < lo { lo } else if x > hi { hi } else { x };
    proof {
        lemma_clamp_bounds(x as int, lo as int, hi as int);
    }
    r
}

// A verified caller uses the contract, without inlining clamp_value's body.
fn clamp_client() -> (r: u32)
    ensures r == 10,
{
    clamp_value(15, 3, 10)
}

} // verus!

// Ordinary Rust smoke-test harness; outside the verification boundary.
fn main() {
    assert_eq!(clamp_client(), 10);
    assert_eq!(clamp_value(1, 3, 10), 3);
    assert_eq!(clamp_value(7, 3, 10), 7);
    assert_eq!(clamp_value(u32::MAX, 0, u32::MAX), u32::MAX);
    println!("clamp: below / inside / above / max passed");
}
