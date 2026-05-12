// XPECT noErrors ---> ""
package '15_01-Constants' {
	public import MeasurementReferences::*;
    public import SI::*;
    public import RealFunctions::*;

    package 'Mathematical Constants' {
     	
        attribute e: Real {
        	assert constraint { round(e * 1E20) == 271828182845904523536.0 }
        }
        attribute pi: Real {
        	assert constraint { round(pi * 1E20) == 314159265358979323846.0 }
        }
    }

    package 'Fundamental Physical Constants' {    	
        attribute 'fine structure constant'      : DimensionOneValue = 7.2973525693E-3[one];  // 2018 CODATA attribute 7.2973525693E-3;  uncertainty = 0.0000000011E-3
        attribute 'electron to proton mass ratio': DimensionOneValue = 5.44617021487E-4[one]; // 2018 CODATA attribute 5.44617021487E-4; uncertainty = 0.00000000033E-4 
        attribute 'speed of light in vacuum'     : SpeedValue = 299792458[m/s];               // 2018 CODATA attribute 299792458 m s^-1; (exact)
     }

    package 'Global Context' {
        attribute 'nominal earth gravitational acceleration': AccelerationValue = 9.80665['m/s²'];
    }

    package 'Model X Context' {
        attribute 'amplifier gain': DimensionOneValue = 3.5[one];
    }
}

