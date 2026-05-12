package pkg {
	part def ABlock;
	action def AnActivity;
	action def B {
		// XPECT errors --> "An action must be typed by action definitions." at "action a: ABlock;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Action, Part" at "action a: ABlock;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "action a: ABlock;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "action a: ABlock;"
		--- */
		action a: ABlock;
		// XPECT errors --> "An action must be typed by action definitions." at "action b: ABlock, AnActivity;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Action, Part" at "action b: ABlock, AnActivity;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "action b: ABlock, AnActivity;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "action b: ABlock, AnActivity;"
		--- */
		action b: ABlock, AnActivity;
	}
	
	ref b : B;
	
	// XPECT errors --> "Must reference an action." at "b"
	perform b;
	
	// XPECT errors --> "An action must be typed by action definitions." at "perform b.a;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Action, Part" at "perform b.a;"
		   "Duplicate of inherited member name 'start' from Action, Part" at "perform b.a;"
		   "Duplicate of inherited member name 'done' from Action, Part" at "perform b.a;"
		   "Duplicate of inherited member name 'self' from Action, Part" at "b.a"
		   "Duplicate of inherited member name 'start' from Action, Part" at "b.a"
		   "Duplicate of inherited member name 'done' from Action, Part" at "b.a"
		--- */
	perform b.a;
}
