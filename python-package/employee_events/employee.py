# Import the QueryBase class
from .query_base import QueryBase

# Import pandas
import pandas as pd


# Define a subclass of QueryBase called Employee
class Employee(QueryBase):

    # Set class attribute
    name = "employee"


    # Method 1: Return all employee names and ids
    def names(self):

        query = """
                SELECT first_name || ' ' || last_name AS full_name,
                       employee_id
                FROM employee
                """

        return self.execute_query(query)


    # Method 2: Return full name for specific employee
    def username(self, id):

        query = f"""
                SELECT first_name || ' ' || last_name AS full_name
                FROM employee
                WHERE employee_id = {id}
                """

        return self.execute_query(query)


    # Method 3: Return ML model dataset as pandas DataFrame
    def model_data(self, id):

        query = f"""
                    SELECT SUM(positive_events) positive_events,
                           SUM(negative_events) negative_events
                    FROM {self.name}
                    JOIN employee_events
                        USING({self.name}_id)
                    WHERE {self.name}.{self.name}_id = {id}
                """

        data = self.execute_query(query)

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=["positive_events", "negative_events"])

        return df
