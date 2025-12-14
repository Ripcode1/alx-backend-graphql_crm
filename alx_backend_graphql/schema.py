"""
Main GraphQL Schema
Combines all app schemas
"""
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    """Main Query class combining all queries"""
    pass


class Mutation(CRMMutation, graphene.ObjectType):
    """Main Mutation class combining all mutations"""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
