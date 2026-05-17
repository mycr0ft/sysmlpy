/*
 * Minimal Activity Test Case
 * 
 * This parses successfully but doesn't extract nested actions or parameters.
 */

package MinimalActivityTest {
    
    action def SimpleActivity {
        // These parameters should be accessible but aren't
        in inputParam : Real;
        out outputParam : Boolean;
        
        // These nested actions should be accessible but aren't
        action stepOne {
            in data : Real;
        }
        
        action stepTwo {
            out result : Boolean;
        }
    }
}
