use vstd::prelude::*;

verus! {

spec fn can_reserve(used: int, limit: int, amount: int) -> bool {
    used + amount <= limit
}

spec fn next_used(used: int, limit: int, amount: int) -> int {
    if can_reserve(used, limit, amount) { used + amount } else { used }
}

proof fn lemma_reservation_preserves_bound(used: int, limit: int, amount: int)
    requires 0 <= used <= limit, 0 <= amount,
    ensures 0 <= next_used(used, limit, amount) <= limit,
{
}

struct Quota {
    used: u64,
    limit: u64,
}

impl Quota {
    spec fn valid(&self) -> bool {
        self.used <= self.limit
    }

    fn new(limit: u64) -> (q: Self)
        ensures q.valid(), q.used == 0, q.limit == limit,
    {
        Quota { used: 0, limit }
    }

    fn reserve(&mut self, amount: u64) -> (accepted: bool)
        requires self.valid(),
        ensures
            final(self).valid(),
            final(self).limit == old(self).limit,
            final(self).used as int == next_used(
                old(self).used as int, old(self).limit as int, amount as int),
            accepted == can_reserve(
                old(self).used as int, old(self).limit as int, amount as int),
    {
        proof {
            lemma_reservation_preserves_bound(
                self.used as int, self.limit as int, amount as int);
        }
        // Avoid computing used + amount before knowing that it fits.
        if amount <= self.limit - self.used {
            self.used = self.used + amount;
            true
        } else {
            false
        }
    }
}

// Check composition: the rejected request must leave the quota unchanged.
fn quota_client() -> (used: u64)
    ensures used == 6,
{
    let mut q = Quota::new(10);
    let first = q.reserve(6);
    assert(first);
    let second = q.reserve(5);
    assert(!second);
    assert(q.valid());
    q.used
}

} // verus!

// This harness is ordinary, unverified Rust and supplies valid inputs.
fn main() {
    assert_eq!(quota_client(), 6);
    let mut q = Quota::new(u64::MAX);
    assert!(q.reserve(u64::MAX));
    assert!(!q.reserve(1));
    assert_eq!(q.used, u64::MAX);
    assert!(q.reserve(0));
    println!("quota: accept / reject / max / zero passed");
}
