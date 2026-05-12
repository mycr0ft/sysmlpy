package 'Hop-through' {
	port p;
	
	part A {
		p :>> p;
	}
	
	part B :> A {
// XPECT noErrors ---> ""
		p :>> 'Hop-through'::p;
	}
}