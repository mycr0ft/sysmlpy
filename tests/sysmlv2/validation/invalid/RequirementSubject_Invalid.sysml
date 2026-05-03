package 'Requirement Subjects' {
	
	requirement def R {
		subject s1;
		
		// XPECT errors --> "Only one subject is allowed." at "subject s2;"
		subject s2;
	}
	
	requirement r: R {
		subject s3;
		
		// XPECT errors --> "Only one subject is allowed." at "subject s4;"
		subject s4;
	}
	
	requirement def R1 :> R {
		in x;
		
		// XPECT errors --> "Subject must be first parameter." at "subject s5;"
		subject s5;
	}
	
	requirement r1 : R1 {
		in y;
		
		// XPECT errors --> "Subject must be first parameter." at "subject s6;"
		subject s6;		
	}
	
}