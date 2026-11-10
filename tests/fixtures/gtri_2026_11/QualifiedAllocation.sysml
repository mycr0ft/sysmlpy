package QualifiedAllocation {
    package Architecture {
        part def Source;
    }

    package Functions {
        action def Target;

        allocate Architecture::Source to Target;
    }
}
