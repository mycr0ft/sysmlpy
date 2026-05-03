package P {
	part def A;	
	
	abstract flow def F;
	abstract flow def G;
	
	abstract flow def H {
		end a;
	}
	
	flow def I :> H {
		end a;
		end b;
		// XPECT errors --> "A flow connection definition can have at most two ends." at "end c;"
		end c;
	}
	
	// XPECT errors --> "A flow connection definition can have at most two ends." at "flow def J :> I;"
	flow def J :> I;
	
	part apart : A {
		part b;
		part c;
		
		message : F from b to c;
		message : F, G from b to c;
		
		// XPECT errors --> "A flow connection must be typed by flow connection definitions." at "message :A from b to c;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Action, Part" at "message :A from b to c;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "message :A from b to c;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "message :A from b to c;"
		--- */
		message :A from b to c;
		// XPECT errors --> "A flow connection must be typed by flow connection definitions." at "message :apart from b to c;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Action, Part" at "message :apart from b to c;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "message :apart from b to c;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "message :apart from b to c;"
		--- */
		message :apart from b to c;
	}
}

