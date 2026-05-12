// XPECT noErrors ---> ""
package 'Requirement Definitions' {

	requirement def Rdef;
	requirement def <'1'> R1def;
	requirement def <'2'> R2def  :> Rdef;
	
	requirement <'1.1'> r11 : R1def;
	requirement <'2.2'> r12 : R2def;

}
