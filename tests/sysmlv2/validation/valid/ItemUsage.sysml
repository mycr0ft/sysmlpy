// XPECT noErrors ---> ""
package 'Items Example' {
	item def A {
		item a; // typed by default item def Item
		item b : B;
		item c: C; // typed by part def, which is a kind of item def
	}
	item def B;	
	part def C;
}