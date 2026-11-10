package QualifiedAllocationImported {
    package Architecture {
        part def Source;
    }

    package Functions {
        private import QualifiedAllocationImported::Architecture::*;
        action def Target;
        allocate Source to Target;
    }
}
