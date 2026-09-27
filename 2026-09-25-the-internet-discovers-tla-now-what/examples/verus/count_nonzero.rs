use vstd::prelude::*;

verus! {

// Total mathematical function: out-of-range prefix lengths map to zero.
// Callers use only 0 <= n <= s.len().
spec fn count_prefix(s: Seq<u32>, n: nat) -> nat
    decreases n,
{
    if n == 0 || n > s.len() {
        0
    } else {
        count_prefix(s, (n - 1) as nat)
            + if s[n as int - 1] != 0 { 1nat } else { 0nat }
    }
}

// Induction over n, written as a recursive proof function.
proof fn lemma_count_bound(s: Seq<u32>, n: nat)
    requires n <= s.len(),
    ensures count_prefix(s, n) <= n,
    decreases n,
{
    if n > 0 {
        lemma_count_bound(s, (n - 1) as nat);
    }
}

fn count_nonzero(values: &Vec<u32>) -> (count: usize)
    ensures
        count as nat == count_prefix(values@, values@.len()),
        count <= values.len(),
{
    let mut i: usize = 0;
    let mut count: usize = 0;
    while i < values.len()
        invariant
            i <= values.len(),
            count as nat == count_prefix(values@, i as nat),
        decreases values.len() - i,
    {
        proof {
            lemma_count_bound(values@, i as nat);
            assert(count_prefix(values@, (i + 1) as nat)
                == count_prefix(values@, i as nat)
                    + if values@[i as int] != 0 { 1nat } else { 0nat });
        }
        if values[i] != 0 {
            count = count + 1;
        }
        i = i + 1;
    }
    proof {
        lemma_count_bound(values@, i as nat);
    }
    count
}

} // verus!

// Runtime examples supplement the proof; they are not the proof itself.
fn main() {
    assert_eq!(count_nonzero(&vec![]), 0);
    assert_eq!(count_nonzero(&vec![0, 0]), 0);
    assert_eq!(count_nonzero(&vec![7, 0, 9, 0, u32::MAX]), 3);
    assert_eq!(count_nonzero(&vec![1, 2, 3]), 3);
    println!("count_nonzero: empty / zero / mixed / all passed");
}
