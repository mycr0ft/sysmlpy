// XPECT noErrors ---> ""
package 'Port Example' {
	part def ABlock;
	port def OutPort {
		out ref anout : ABlock;
		in ref ain : ABlock;
	}
	port def InPort;
	part def ABlock1 {
		port aport : OutPort;
	}
	part def ABlock2 {
		port aport : ~InPort;
	}
	part tank: ABlock1 {
		port aredefinedport redefines aport {
			out ref redefines anout;
			in ref redefines ain;
		}	
	}
}
