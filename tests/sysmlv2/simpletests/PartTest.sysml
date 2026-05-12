// XPECT noErrors ---> ""
package PartTest {
	
	part f: A;

	public part def A {
		part <'1'> b: B;
		protected port c: C;
		constant attribute x;
		derived constant ref attribute y :> x;
		ref z;
	}
	
	item def S;
	
	abstract part def <xx> B {
		public abstract part a: A;
		public abstract part b subsets a;
		public abstract part c subsets a;
		port x: ~C {
		    port p;
		    ref port q;
		}
		package P { }
	}
	
	private port def C {
		private in ref y: A, B {
		    part B_b redefines B::b;
		    part B_c redefines B::c;
		    port B_x redefines B::x;
		}
		alias z1 for y;
		alias z2 for y;
		port c1 : C;
		ref port c2 : C;
	}
	
    part p1 :> p2;
    part p2 :> p3; 
    part p3 :> p1;
    
    part p4 :> p4;
	
}
