// XPECT noErrors ---> ""
package BindingConnectorExample {
	part def B0;
	part def B1; 
	part def V;
	part v : V {
		part b0 : B0 {
			port p0 {
				in ref myIn;
				out ref myOut;
			}
		}
		part b1 : B1 {
			port p1 {
				in ref myIn;
				out ref myOut;
			}
		}
		//in[Part, Object] out[Part, Object]
		bind b0.p0.myIn = b1.p1.myOut;
		bind b0.p0.myOut = b1.p1.myIn;
		//inin
		bind b0.p0.myIn = b1.p1.myIn;
		bind b0.p0.myOut = b1.p1.myOut;
		//outout
		bind b0.p0.myIn = b1.p1.myOut;
		bind b0.p0.myOut = b1.p1.myIn;
		
	} 
}
