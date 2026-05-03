package 'Case Subjects and Objectives' {
	
	case def C {
		subject s1;
		
		// XPECT errors --> "Only one subject is allowed." at "subject s2;"
		subject s2;

		objective o1;
		
		// XPECT errors --> "Only one objective is allowed." at "objective o2;"
		objective o2;
	}
	
	case c: C {
		subject s3;
		
		// XPECT errors --> "Only one subject is allowed." at "subject s4;"
		subject s4;

		// XPECT errors --> "Only one objective is allowed." at "objective o3;"
		objective o3;
		
		// XPECT errors --> "Only one objective is allowed." at "objective o4;"
		objective o4;
	}
	
	case def C1 :> C {
		in x;
		
		// XPECT errors --> "Subject must be first parameter." at "subject s5;"
		subject s5;
		
		// XPECT errors --> "Only one objective is allowed." at "objective o5;"
		objective o5;
	}
	
	//* XPECT errors ---
		"Only one objective is allowed." at "case c1 : C1;"
		"Subject must be first parameter." at "case c1 : C1;"
	   ---
	*/
	case c1 : C1;
	
	case c2 {
		in y;
		
		// XPECT errors --> "Subject must be first parameter." at "subject s6;"
		subject s6;
	}
	
}