// XPECT noErrors ---> ""
package EnumerationTest {
	
	attribute def Color {
		attribute val : ScalarValues::Natural;
	}
	
	enum def ColorKind :> Color {
		enum red {
			:>> val = 0;
		}
		enum blue {
			:>> val = 1;
		}
		enum green {
			:>> val = 2;
		}
	}
	
	enum color : ColorKind;
	enum color1 = ColorKind::blue;	// Implicitly typed by ColorKind.
	attribute color2 : ColorKind = color1;
	
	enum def E1 { a; b; c; }
	enum def E2;
	
	attribute def Size :> ScalarValues::Real;		
	enum def SizeChoice :> Size {
		= 60.0;
		= 70.0;
		= 80.0;
	}	
	enum size: SizeChoice = 60.0;
	
}