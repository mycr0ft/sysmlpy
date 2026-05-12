package 'Individuals and Roles' {
	
	part def A;
	part def B;
	part def BB :> B;
	part def C;
	
	individual def AA :> BB;
	individual def CC :> A;
	individual def DD;

	individual def A_1 :> A {
		part b_1 : B;
		part c_1 : C;
	}
	individual def B_1 :> B;
	
	// XPECT errors --> "At most one individual definition is allowed." at "individual two_types : A_1, B_1;"
	individual two_types : A_1, B_1;

	// XPECT errors -->"An individual must be typed by one individual definition." at "individual b_1_1 : B;"
	individual b_1_1 : B;
	
}