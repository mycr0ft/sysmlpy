package TransitionUsage_invalid {
	
	state def S1 parallel {
		state S1_1;
		// XPECT errors ---> "A parallel state cannot have successions or transitions." at "then S1_2;"
		then S1_2;
		state S1_2;
	}
	
	item def A;

	state def S2 {
		entry action init;
		// XPECT errors ---> "A transition with an accepter must have a state as its source." at "accept A"
		transition init accept A then S2_1;
		
		state S2_1;
		transition
			first S2_1
			// XPECT errors ---> "Must be a Boolean expression." at "if \"test\""
			if "test"
			then S2_2;
		state S2_2;
	}
	
	state s1 parallel {
		state s1_1;
		// XPECT errors ---> "A parallel state cannot have successions or transitions." at "then s1_2;"
		then s1_2;
		state s1_2;
	}
}
