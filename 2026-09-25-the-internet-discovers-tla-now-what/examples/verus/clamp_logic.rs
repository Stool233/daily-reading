use vstd::prelude::*;

verus! {

// A mathematical value: same definition as the first clamp example.
spec fn clamp_spec(x: int, lo: int, hi: int) -> int {
    if x < lo { lo } else if x > hi { hi } else { x }
}

// A proposition about an input/output tuple, written using implication.
spec fn is_clamped(x: int, lo: int, hi: int, r: int) -> bool {
    lo <= hi
        && (x < lo ==> r == lo)
        && (lo <= x && x <= hi ==> r == x)
        && (x > hi ==> r == hi)
}

proof fn lemma_forms_agree(x: int, lo: int, hi: int, r: int)
    requires lo <= hi,
    ensures is_clamped(x, lo, hi, r) <==> (r == clamp_spec(x, lo, hi)),
{
}

proof fn lemma_exists_unique(x: int, lo: int, hi: int)
    requires lo <= hi,
    ensures
        exists|r: int| is_clamped(x, lo, hi, r),
        forall|a: int, b: int|
            is_clamped(x, lo, hi, a) && is_clamped(x, lo, hi, b) ==> a == b,
{
    let r = clamp_spec(x, lo, hi);
    lemma_forms_agree(x, lo, hi, r);
    assert(is_clamped(x, lo, hi, r));
    assert forall|a: int, b: int|
        is_clamped(x, lo, hi, a) && is_clamped(x, lo, hi, b) implies a == b by {
        lemma_forms_agree(x, lo, hi, a);
        lemma_forms_agree(x, lo, hi, b);
    }
}

proof fn lemma_all_bounds()
    ensures forall|x: int, lo: int, hi: int|
        lo <= hi ==> lo <= #[trigger] clamp_spec(x, lo, hi) <= hi,
{
}

// Different program structure: two successive updates instead of a nested if.
fn clamp_in_two_steps(x: u32, lo: u32, hi: u32) -> (r: u32)
    requires lo <= hi,
    ensures
        is_clamped(x as int, lo as int, hi as int, r as int),
        r as int == clamp_spec(x as int, lo as int, hi as int),
{
    let mut r = x;
    if r < lo {
        r = lo;
    }
    if r > hi {
        r = hi;
    }
    proof {
        lemma_forms_agree(x as int, lo as int, hi as int, r as int);
    }
    r
}

// This satisfies its deliberately weak contract, but not the clamp requirement.
fn only_bounds(x: u32, lo: u32, hi: u32) -> (r: u32)
    requires lo <= hi,
    ensures lo <= r <= hi,
{
    lo
}

} // verus!

// Unverified runtime harness, as in the earlier examples.
fn main() {
    assert_eq!(clamp_in_two_steps(1, 3, 10), 3);
    assert_eq!(clamp_in_two_steps(7, 3, 10), 7);
    assert_eq!(clamp_in_two_steps(15, 3, 10), 10);
    assert_eq!(clamp_in_two_steps(7, 5, 5), 5);
    assert_eq!(clamp_in_two_steps(u32::MAX, 0, u32::MAX), u32::MAX);
    assert_eq!(only_bounds(7, 3, 10), 3);
    assert_ne!(only_bounds(7, 3, 10), clamp_in_two_steps(7, 3, 10));
    println!("clamp_logic: alternate implementation passed; weak contract accepts a non-clamp result");
}
