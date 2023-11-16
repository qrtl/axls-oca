Using this Module:

When working with the crm.lead model, you can establish standard exception handling
by defining rules based on specific criteria. (Standard exception handling means
the module automatically checks all exception rules associated with the current record model, crm.lead.)

Additionally, the module offers advanced exception control for CRM stages. As you navigate to CRM > Stages,
you can create or edit a stage and use the ignore_exception option to bypass standard checks for that stage if needed.
Moreover, by defining specific exception rules in the exception_ids field for a stage, these rules will exclusively be checked
for that stage, providing a more tailored approach. If the exception_ids field is left empty, the stage will follow standard behavior
and check all exceptions.
