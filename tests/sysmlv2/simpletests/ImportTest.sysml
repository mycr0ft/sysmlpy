// XPECT noErrors ---> ""
package ImportTest {
    package Pkg1 {
    	public import Pkg2::Pkg21::Pkg211::P211;
    	public import Pkg2::Pkg21::*;
    	public import Pkg211::*::**;
        part p11 : Pkg211::P211;
        part def P12;
    }

    package Pkg2 {
        public import Pkg1::*;
        package Pkg21 {
        	package Pkg211 {
        		part def P211 :> P12;
        	}
        }
    }
}