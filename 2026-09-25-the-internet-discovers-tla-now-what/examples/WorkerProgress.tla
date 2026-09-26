-------------------------- MODULE WorkerProgress --------------------------
\* An original reading exercise; not the article's leader-election model.
CONSTANT AllowStart
VARIABLES phase, started

vars == <<phase, started>>

Init == /\ phase = "ready"
        /\ started = FALSE

Start == /\ AllowStart
         /\ phase = "ready"
         /\ phase' = "running"
         /\ started' = TRUE

Finish == /\ phase = "running"
          /\ phase' = "done"
          /\ UNCHANGED started

\* Explicit idle steps keep terminal states from being TLC deadlocks.
Wait == UNCHANGED vars

Next == Start \/ Finish \/ Wait
Spec == Init /\ [][Next]_vars
FairSpec == Spec /\ WF_vars(Start) /\ WF_vars(Finish)

TypeOK == /\ phase \in {"ready", "running", "done"}
          /\ started \in BOOLEAN

NoFinishBeforeStart == (phase = "done") => started
Safety == TypeOK /\ NoFinishBeforeStart
EventuallyDone == <>(phase = "done")

\* Two finite experiments about inductiveness, not actual initial states.
InductiveSafety == TypeOK /\ (started = (phase # "ready"))
SafetyAsInitial == Safety /\ [][Next]_vars
StrongAsInitial == InductiveSafety /\ [][Next]_vars
=============================================================================
