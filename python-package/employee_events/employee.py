# Import the QueryBase class
from .query_base import QueryBase

# Import dependencies needed for sql execution
from .sql_execution import QueryMixin


# Define a subclass of QueryBase
# called Employee
class Employee(QueryBase):

    # Set the class attribute `name`
    # to the string "employee"
    name = "employee"


    # Define a method called `names`
    # that receives no arguments
    # This method should return a list of tuples
    # from an sql execution
    def names(self):

        # Query 3
        query = """
        SELECT first_name || ' ' || last_name AS full_name,
               employee_id
        FROM employee
        ORDER BY employee_id
        """

        return self.query(query)


    # Define a method called `username`
    # that receives an `id` argument
    def username(self, id):

        # Query 4
        query = f"""
        SELECT first_name || ' ' || last_name AS full_name
        FROM employee
        WHERE employee_id = {id}
        """

        return self.query(query)


    # Below is method with an SQL query
    # This SQL query generates the data needed for
    # the machine learning model.
    # Without editing the query, alter this method
    # so when it is called, a pandas dataframe
    # is returns containing the execution of
    # the sql query
    def model_data(self, id):

        query = f"""
                    SELECT SUM(positive_events) positive_events
                         , SUM(negative_events) negative_events
                    FROM {self.name}
                    JOIN employee_events
                        USING({self.name}_id)
                    WHERE {self.name}.{self.name}_id = {id}
                """

        return self.pandas_query(query)