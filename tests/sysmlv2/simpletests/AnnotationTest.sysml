// XPECT noErrors ---> ""
package AnalysisAnnotation {
	public import ScalarValues::Real;
	public import AnalysisTooling::*;
	
	action def ComputeDynamics {
		metadata ToolExecution {
			toolName = "ModelCenter";
			uri = "aserv://localhost/Vehicle/Equation1";
		}
			
		in dt : Real          { @ToolVariable { name = "deltaT"; } }
		in whlpwr : Real      { @ToolVariable { name = "power"; } }
		in Cd : Real          { @ToolVariable { name = "C_D"; } }
		in Cf : Real          { @ToolVariable { name = "C_F"; } }
		in tm : Real          { @ToolVariable { name = "mass"; } }
		in v_in : Real        { @ToolVariable { name = "v0"; } }
		in x_in : Real        { @ToolVariable { name = "x0"; } }
		
		out a_out : Real      { @ToolVariable { name = "a"; } }
		out v_out : Real      { @ToolVariable { name = "v"; } }
		out x_out : Real      { @ToolVariable { name = "x"; } }
			
	}

}