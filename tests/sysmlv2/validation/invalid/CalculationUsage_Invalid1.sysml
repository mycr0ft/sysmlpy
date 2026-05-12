package pkg {
	calc def 'F1';
	calc def 'F2';
	action def B;
	action bb: B;
	part def A {
		// XPECT errors --> "A calculation must be typed by one calculation definition." at "calc f1 : F1, F2;"
	 	calc f1 : F1, F2;
	 	/* XPECT errors --- 
	 	   "A calculation must be typed by one calculation definition." at "calc f2 : A;"
		--- */ 
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Calculation, Part" at "calc f2 : A;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "calc f2 : A;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "calc f2 : A;"
		--- */
    	calc f2: A;
    	// XPECT errors ---> "A calculation must be typed by one calculation definition." at "calc f3 : f2;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Calculation, Part" at "calc f3 : f2;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "calc f3 : f2;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "calc f3 : f2;"
		--- */
    	calc f3: f2;
    	// XPECT errors ---> "A calculation must be typed by one calculation definition." at "calc f4 : A::f1;"
    	calc f4: A::f1;
    	// XPECT errors ---> "A calculation must be typed by one calculation definition." at "calc f5 : B;"
    	calc f5: B;
    	// XPECT errors ---> "A calculation must be typed by one calculation definition." at "calc f6 : bb;"
    	calc f6: bb;
   	}
}