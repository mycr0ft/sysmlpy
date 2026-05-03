package ImportVisibility {
	public import ScalarValues;
	private import ScalarValues;
	protected import ScalarValues;
	// XPECT errors ---> "mismatched input 'import' expecting '}'" at "import"
	import ScalarValues;
	// XPECT errors ---> "extraneous input '}' expecting EOF" at "}"
}