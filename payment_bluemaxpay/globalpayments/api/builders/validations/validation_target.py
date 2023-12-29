from odoo.addons.payment_bluemaxpay.globalpayments import api
from odoo.addons.payment_bluemaxpay.globalpayments.api.builders.validations.validation_clause import ValidationClause


class ValidationTarget(object):
    parent = None
    precondition = None
    clause = None

    type_name = None
    constraint_name = None
    constraint_value = None

    def __init__(self, parent, type_name):
        self.parent = parent
        self.type_name = type_name

    def with_constraint(self, name, value):
        self.constraint_name = name
        self.constraint_value = value
        return self

    def check(self, property_name):
        if property_name is None:
            raise api.entities.exceptions.BuilderException()

        self.clause = ValidationClause(self.parent, self, property_name)
        return self.clause

    def when(self, property_name):
        if property_name is None:
            raise api.entities.exceptions.BuilderException()

        self.precondition = ValidationClause(self.parent, self, property_name,
                                             True)
        return self.precondition
