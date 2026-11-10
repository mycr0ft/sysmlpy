package TypedAllocation {
    package Architecture {
        part def Source;
    }

    package Functions {
        action def Target;

        allocation def SourceToTarget {
            end :>> source : Architecture::Source;
            end :>> target : Target;
            allocate source to target;
        }
    }
}
