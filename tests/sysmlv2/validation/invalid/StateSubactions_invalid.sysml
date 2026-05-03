package 'State Subactions' {
	
	state def S {
		entry action a;
		do action b;
		exit action c;
		
		//XPECT errors --> "A state may have at most one exit action." at "exit action c1;"	
		exit action c1;
		//XPECT errors --> "A state may have at most one entry action." at "entry action a1;"	
		entry action a1;
		//XPECT errors --> "A state may have at most one do action." at "do action b1;"	
		do action b1;
	}
	
	state s {
		entry action a;
		do action b;
		exit action c;
		
		//XPECT errors --> "A state may have at most one exit action." at "exit action c1;"	
		exit action c1;
		//XPECT errors --> "A state may have at most one entry action." at "entry action a1;"	
		entry action a1;
		//XPECT errors --> "A state may have at most one do action." at "do action b1;"	
		do action b1;
	}
	
}
