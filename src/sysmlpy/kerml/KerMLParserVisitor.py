# Generated from KerMLParser.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .KerMLParser import KerMLParser
else:
    from KerMLParser import KerMLParser

# This class defines a complete generic visitor for a parse tree produced by KerMLParser.

class KerMLParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by KerMLParser#ownedExpression.
    def visitOwnedExpression(self, ctx:KerMLParser.OwnedExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeReference.
    def visitTypeReference(self, ctx:KerMLParser.TypeReferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#sequenceExpressionList.
    def visitSequenceExpressionList(self, ctx:KerMLParser.SequenceExpressionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#baseExpression.
    def visitBaseExpression(self, ctx:KerMLParser.BaseExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#nullExpression.
    def visitNullExpression(self, ctx:KerMLParser.NullExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureReferenceExpression.
    def visitFeatureReferenceExpression(self, ctx:KerMLParser.FeatureReferenceExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#constructorExpression.
    def visitConstructorExpression(self, ctx:KerMLParser.ConstructorExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#bodyExpression.
    def visitBodyExpression(self, ctx:KerMLParser.BodyExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#argumentList.
    def visitArgumentList(self, ctx:KerMLParser.ArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#positionalArgumentList.
    def visitPositionalArgumentList(self, ctx:KerMLParser.PositionalArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namedArgumentList.
    def visitNamedArgumentList(self, ctx:KerMLParser.NamedArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namedArgument.
    def visitNamedArgument(self, ctx:KerMLParser.NamedArgumentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#literalExpression.
    def visitLiteralExpression(self, ctx:KerMLParser.LiteralExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#literalBoolean.
    def visitLiteralBoolean(self, ctx:KerMLParser.LiteralBooleanContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#literalString.
    def visitLiteralString(self, ctx:KerMLParser.LiteralStringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#literalInteger.
    def visitLiteralInteger(self, ctx:KerMLParser.LiteralIntegerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#literalReal.
    def visitLiteralReal(self, ctx:KerMLParser.LiteralRealContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#literalInfinity.
    def visitLiteralInfinity(self, ctx:KerMLParser.LiteralInfinityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#argumentMember.
    def visitArgumentMember(self, ctx:KerMLParser.ArgumentMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#argumentExpressionMember.
    def visitArgumentExpressionMember(self, ctx:KerMLParser.ArgumentExpressionMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#name.
    def visitName(self, ctx:KerMLParser.NameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#unreservedKeyword.
    def visitUnreservedKeyword(self, ctx:KerMLParser.UnreservedKeywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#identification.
    def visitIdentification(self, ctx:KerMLParser.IdentificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#relationshipBody.
    def visitRelationshipBody(self, ctx:KerMLParser.RelationshipBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#relationshipOwnedElement.
    def visitRelationshipOwnedElement(self, ctx:KerMLParser.RelationshipOwnedElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedRelatedElement.
    def visitOwnedRelatedElement(self, ctx:KerMLParser.OwnedRelatedElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#dependency.
    def visitDependency(self, ctx:KerMLParser.DependencyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#annotation.
    def visitAnnotation(self, ctx:KerMLParser.AnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedAnnotation.
    def visitOwnedAnnotation(self, ctx:KerMLParser.OwnedAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#annotatingElement.
    def visitAnnotatingElement(self, ctx:KerMLParser.AnnotatingElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#comment.
    def visitComment(self, ctx:KerMLParser.CommentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#documentation.
    def visitDocumentation(self, ctx:KerMLParser.DocumentationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#textualRepresentation.
    def visitTextualRepresentation(self, ctx:KerMLParser.TextualRepresentationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#rootNamespace.
    def visitRootNamespace(self, ctx:KerMLParser.RootNamespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespace.
    def visitNamespace(self, ctx:KerMLParser.NamespaceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceDeclaration.
    def visitNamespaceDeclaration(self, ctx:KerMLParser.NamespaceDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceBody.
    def visitNamespaceBody(self, ctx:KerMLParser.NamespaceBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceBodyElement.
    def visitNamespaceBodyElement(self, ctx:KerMLParser.NamespaceBodyElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#memberPrefix.
    def visitMemberPrefix(self, ctx:KerMLParser.MemberPrefixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#visibilityIndicator.
    def visitVisibilityIndicator(self, ctx:KerMLParser.VisibilityIndicatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceMember.
    def visitNamespaceMember(self, ctx:KerMLParser.NamespaceMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#nonFeatureMember.
    def visitNonFeatureMember(self, ctx:KerMLParser.NonFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceFeatureMember.
    def visitNamespaceFeatureMember(self, ctx:KerMLParser.NamespaceFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#aliasMember.
    def visitAliasMember(self, ctx:KerMLParser.AliasMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#qualifiedName.
    def visitQualifiedName(self, ctx:KerMLParser.QualifiedNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#importRule.
    def visitImportRule(self, ctx:KerMLParser.ImportRuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#importDeclaration.
    def visitImportDeclaration(self, ctx:KerMLParser.ImportDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#membershipImport.
    def visitMembershipImport(self, ctx:KerMLParser.MembershipImportContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceImport.
    def visitNamespaceImport(self, ctx:KerMLParser.NamespaceImportContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#filterPackage.
    def visitFilterPackage(self, ctx:KerMLParser.FilterPackageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#filterPackageMember.
    def visitFilterPackageMember(self, ctx:KerMLParser.FilterPackageMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#memberElement.
    def visitMemberElement(self, ctx:KerMLParser.MemberElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#nonFeatureElement.
    def visitNonFeatureElement(self, ctx:KerMLParser.NonFeatureElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureElement.
    def visitFeatureElement(self, ctx:KerMLParser.FeatureElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#type.
    def visitType(self, ctx:KerMLParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typePrefix.
    def visitTypePrefix(self, ctx:KerMLParser.TypePrefixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeDeclaration.
    def visitTypeDeclaration(self, ctx:KerMLParser.TypeDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#specializationPart.
    def visitSpecializationPart(self, ctx:KerMLParser.SpecializationPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#conjugationPart.
    def visitConjugationPart(self, ctx:KerMLParser.ConjugationPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeRelationshipPart.
    def visitTypeRelationshipPart(self, ctx:KerMLParser.TypeRelationshipPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#disjoiningPart.
    def visitDisjoiningPart(self, ctx:KerMLParser.DisjoiningPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#unioningPart.
    def visitUnioningPart(self, ctx:KerMLParser.UnioningPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#intersectingPart.
    def visitIntersectingPart(self, ctx:KerMLParser.IntersectingPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#differencingPart.
    def visitDifferencingPart(self, ctx:KerMLParser.DifferencingPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeBody.
    def visitTypeBody(self, ctx:KerMLParser.TypeBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeBodyElement.
    def visitTypeBodyElement(self, ctx:KerMLParser.TypeBodyElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#specialization.
    def visitSpecialization(self, ctx:KerMLParser.SpecializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedSpecialization.
    def visitOwnedSpecialization(self, ctx:KerMLParser.OwnedSpecializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#specificType.
    def visitSpecificType(self, ctx:KerMLParser.SpecificTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#generalType.
    def visitGeneralType(self, ctx:KerMLParser.GeneralTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#conjugation.
    def visitConjugation(self, ctx:KerMLParser.ConjugationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedConjugation.
    def visitOwnedConjugation(self, ctx:KerMLParser.OwnedConjugationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#disjoining.
    def visitDisjoining(self, ctx:KerMLParser.DisjoiningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedDisjoining.
    def visitOwnedDisjoining(self, ctx:KerMLParser.OwnedDisjoiningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#unioning.
    def visitUnioning(self, ctx:KerMLParser.UnioningContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#intersecting.
    def visitIntersecting(self, ctx:KerMLParser.IntersectingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#differencing.
    def visitDifferencing(self, ctx:KerMLParser.DifferencingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureMember.
    def visitFeatureMember(self, ctx:KerMLParser.FeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeFeatureMember.
    def visitTypeFeatureMember(self, ctx:KerMLParser.TypeFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedFeatureMember.
    def visitOwnedFeatureMember(self, ctx:KerMLParser.OwnedFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#classifier.
    def visitClassifier(self, ctx:KerMLParser.ClassifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#classifierDeclaration.
    def visitClassifierDeclaration(self, ctx:KerMLParser.ClassifierDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#superclassingPart.
    def visitSuperclassingPart(self, ctx:KerMLParser.SuperclassingPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#subclassification.
    def visitSubclassification(self, ctx:KerMLParser.SubclassificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedSubclassification.
    def visitOwnedSubclassification(self, ctx:KerMLParser.OwnedSubclassificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#feature.
    def visitFeature(self, ctx:KerMLParser.FeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#endFeaturePrefix.
    def visitEndFeaturePrefix(self, ctx:KerMLParser.EndFeaturePrefixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#basicFeaturePrefix.
    def visitBasicFeaturePrefix(self, ctx:KerMLParser.BasicFeaturePrefixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featurePrefix.
    def visitFeaturePrefix(self, ctx:KerMLParser.FeaturePrefixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedCrossFeatureMember.
    def visitOwnedCrossFeatureMember(self, ctx:KerMLParser.OwnedCrossFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedCrossFeature.
    def visitOwnedCrossFeature(self, ctx:KerMLParser.OwnedCrossFeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureDirection.
    def visitFeatureDirection(self, ctx:KerMLParser.FeatureDirectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureDeclaration.
    def visitFeatureDeclaration(self, ctx:KerMLParser.FeatureDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureIdentification.
    def visitFeatureIdentification(self, ctx:KerMLParser.FeatureIdentificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureRelationshipPart.
    def visitFeatureRelationshipPart(self, ctx:KerMLParser.FeatureRelationshipPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#chainingPart.
    def visitChainingPart(self, ctx:KerMLParser.ChainingPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#invertingPart.
    def visitInvertingPart(self, ctx:KerMLParser.InvertingPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeFeaturingPart.
    def visitTypeFeaturingPart(self, ctx:KerMLParser.TypeFeaturingPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureSpecializationPart.
    def visitFeatureSpecializationPart(self, ctx:KerMLParser.FeatureSpecializationPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#multiplicityPart.
    def visitMultiplicityPart(self, ctx:KerMLParser.MultiplicityPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureSpecialization.
    def visitFeatureSpecialization(self, ctx:KerMLParser.FeatureSpecializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typings.
    def visitTypings(self, ctx:KerMLParser.TypingsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typedBy.
    def visitTypedBy(self, ctx:KerMLParser.TypedByContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#subsettings.
    def visitSubsettings(self, ctx:KerMLParser.SubsettingsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#subsets.
    def visitSubsets(self, ctx:KerMLParser.SubsetsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#references.
    def visitReferences(self, ctx:KerMLParser.ReferencesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#crosses.
    def visitCrosses(self, ctx:KerMLParser.CrossesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#redefinitions.
    def visitRedefinitions(self, ctx:KerMLParser.RedefinitionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#redefines.
    def visitRedefines(self, ctx:KerMLParser.RedefinesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureTyping.
    def visitFeatureTyping(self, ctx:KerMLParser.FeatureTypingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedFeatureTyping.
    def visitOwnedFeatureTyping(self, ctx:KerMLParser.OwnedFeatureTypingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#subsetting.
    def visitSubsetting(self, ctx:KerMLParser.SubsettingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedSubsetting.
    def visitOwnedSubsetting(self, ctx:KerMLParser.OwnedSubsettingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedReferenceSubsetting.
    def visitOwnedReferenceSubsetting(self, ctx:KerMLParser.OwnedReferenceSubsettingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedCrossSubsetting.
    def visitOwnedCrossSubsetting(self, ctx:KerMLParser.OwnedCrossSubsettingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#redefinition.
    def visitRedefinition(self, ctx:KerMLParser.RedefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedRedefinition.
    def visitOwnedRedefinition(self, ctx:KerMLParser.OwnedRedefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureInverting.
    def visitFeatureInverting(self, ctx:KerMLParser.FeatureInvertingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedFeatureInverting.
    def visitOwnedFeatureInverting(self, ctx:KerMLParser.OwnedFeatureInvertingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#typeFeaturing.
    def visitTypeFeaturing(self, ctx:KerMLParser.TypeFeaturingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedTypeFeaturing.
    def visitOwnedTypeFeaturing(self, ctx:KerMLParser.OwnedTypeFeaturingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#dataType.
    def visitDataType(self, ctx:KerMLParser.DataTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#class.
    def visitClass(self, ctx:KerMLParser.ClassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#structure.
    def visitStructure(self, ctx:KerMLParser.StructureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#association.
    def visitAssociation(self, ctx:KerMLParser.AssociationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#associationStructure.
    def visitAssociationStructure(self, ctx:KerMLParser.AssociationStructureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#connector.
    def visitConnector(self, ctx:KerMLParser.ConnectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#connectorDeclaration.
    def visitConnectorDeclaration(self, ctx:KerMLParser.ConnectorDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#binaryConnectorDeclaration.
    def visitBinaryConnectorDeclaration(self, ctx:KerMLParser.BinaryConnectorDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#naryConnectorDeclaration.
    def visitNaryConnectorDeclaration(self, ctx:KerMLParser.NaryConnectorDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#connectorEndMember.
    def visitConnectorEndMember(self, ctx:KerMLParser.ConnectorEndMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#connectorEnd.
    def visitConnectorEnd(self, ctx:KerMLParser.ConnectorEndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedCrossMultiplicityMember.
    def visitOwnedCrossMultiplicityMember(self, ctx:KerMLParser.OwnedCrossMultiplicityMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedCrossMultiplicity.
    def visitOwnedCrossMultiplicity(self, ctx:KerMLParser.OwnedCrossMultiplicityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#bindingConnector.
    def visitBindingConnector(self, ctx:KerMLParser.BindingConnectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#bindingConnectorDeclaration.
    def visitBindingConnectorDeclaration(self, ctx:KerMLParser.BindingConnectorDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#succession.
    def visitSuccession(self, ctx:KerMLParser.SuccessionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#successionDeclaration.
    def visitSuccessionDeclaration(self, ctx:KerMLParser.SuccessionDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#behavior.
    def visitBehavior(self, ctx:KerMLParser.BehaviorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#step.
    def visitStep(self, ctx:KerMLParser.StepContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#function.
    def visitFunction(self, ctx:KerMLParser.FunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#functionBody.
    def visitFunctionBody(self, ctx:KerMLParser.FunctionBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#functionBodyPart.
    def visitFunctionBodyPart(self, ctx:KerMLParser.FunctionBodyPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#returnFeatureMember.
    def visitReturnFeatureMember(self, ctx:KerMLParser.ReturnFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#resultExpressionMember.
    def visitResultExpressionMember(self, ctx:KerMLParser.ResultExpressionMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#expression.
    def visitExpression(self, ctx:KerMLParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#predicate.
    def visitPredicate(self, ctx:KerMLParser.PredicateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#booleanExpression.
    def visitBooleanExpression(self, ctx:KerMLParser.BooleanExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#invariant.
    def visitInvariant(self, ctx:KerMLParser.InvariantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureChainMember.
    def visitFeatureChainMember(self, ctx:KerMLParser.FeatureChainMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#interaction.
    def visitInteraction(self, ctx:KerMLParser.InteractionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#flow.
    def visitFlow(self, ctx:KerMLParser.FlowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#successionFlow.
    def visitSuccessionFlow(self, ctx:KerMLParser.SuccessionFlowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#flowDeclaration.
    def visitFlowDeclaration(self, ctx:KerMLParser.FlowDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#payloadFeatureMember.
    def visitPayloadFeatureMember(self, ctx:KerMLParser.PayloadFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#payloadFeature.
    def visitPayloadFeature(self, ctx:KerMLParser.PayloadFeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#payloadFeatureSpecializationPart.
    def visitPayloadFeatureSpecializationPart(self, ctx:KerMLParser.PayloadFeatureSpecializationPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#flowEndMember.
    def visitFlowEndMember(self, ctx:KerMLParser.FlowEndMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#flowEnd.
    def visitFlowEnd(self, ctx:KerMLParser.FlowEndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureReferenceMember.
    def visitFeatureReferenceMember(self, ctx:KerMLParser.FeatureReferenceMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedFeatureChainMember.
    def visitOwnedFeatureChainMember(self, ctx:KerMLParser.OwnedFeatureChainMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#flowFeatureMember.
    def visitFlowFeatureMember(self, ctx:KerMLParser.FlowFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureReference.
    def visitFeatureReference(self, ctx:KerMLParser.FeatureReferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedFeatureChain.
    def visitOwnedFeatureChain(self, ctx:KerMLParser.OwnedFeatureChainContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#flowFeature.
    def visitFlowFeature(self, ctx:KerMLParser.FlowFeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#valuePart.
    def visitValuePart(self, ctx:KerMLParser.ValuePartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#featureValue.
    def visitFeatureValue(self, ctx:KerMLParser.FeatureValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#multiplicity.
    def visitMultiplicity(self, ctx:KerMLParser.MultiplicityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#multiplicitySubset.
    def visitMultiplicitySubset(self, ctx:KerMLParser.MultiplicitySubsetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#multiplicityRange.
    def visitMultiplicityRange(self, ctx:KerMLParser.MultiplicityRangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedMultiplicity.
    def visitOwnedMultiplicity(self, ctx:KerMLParser.OwnedMultiplicityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#ownedMultiplicityRange.
    def visitOwnedMultiplicityRange(self, ctx:KerMLParser.OwnedMultiplicityRangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#multiplicityBounds.
    def visitMultiplicityBounds(self, ctx:KerMLParser.MultiplicityBoundsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#multiplicityExpressionMember.
    def visitMultiplicityExpressionMember(self, ctx:KerMLParser.MultiplicityExpressionMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metaclass.
    def visitMetaclass(self, ctx:KerMLParser.MetaclassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#prefixMetadataAnnotation.
    def visitPrefixMetadataAnnotation(self, ctx:KerMLParser.PrefixMetadataAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#prefixMetadataMember.
    def visitPrefixMetadataMember(self, ctx:KerMLParser.PrefixMetadataMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#prefixMetadataFeature.
    def visitPrefixMetadataFeature(self, ctx:KerMLParser.PrefixMetadataFeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metadataFeature.
    def visitMetadataFeature(self, ctx:KerMLParser.MetadataFeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metadataFeatureDeclaration.
    def visitMetadataFeatureDeclaration(self, ctx:KerMLParser.MetadataFeatureDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metadataBody.
    def visitMetadataBody(self, ctx:KerMLParser.MetadataBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metadataBodyElement.
    def visitMetadataBodyElement(self, ctx:KerMLParser.MetadataBodyElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metadataBodyFeatureMember.
    def visitMetadataBodyFeatureMember(self, ctx:KerMLParser.MetadataBodyFeatureMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#metadataBodyFeature.
    def visitMetadataBodyFeature(self, ctx:KerMLParser.MetadataBodyFeatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#package.
    def visitPackage(self, ctx:KerMLParser.PackageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#libraryPackage.
    def visitLibraryPackage(self, ctx:KerMLParser.LibraryPackageContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#packageDeclaration.
    def visitPackageDeclaration(self, ctx:KerMLParser.PackageDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#packageBody.
    def visitPackageBody(self, ctx:KerMLParser.PackageBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#elementFilterMember.
    def visitElementFilterMember(self, ctx:KerMLParser.ElementFilterMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#filterPackageImportDeclaration.
    def visitFilterPackageImportDeclaration(self, ctx:KerMLParser.FilterPackageImportDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#namespaceImportDirect.
    def visitNamespaceImportDirect(self, ctx:KerMLParser.NamespaceImportDirectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by KerMLParser#emptyFeature_.
    def visitEmptyFeature_(self, ctx:KerMLParser.EmptyFeature_Context):
        return self.visitChildren(ctx)



del KerMLParser