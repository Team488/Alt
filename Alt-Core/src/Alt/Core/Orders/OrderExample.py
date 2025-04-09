# an order, otherwise known as a command will be triggered and then run once.
# lifespan: 1. create 2. run 3. close
# NOTE: Orders will get processwide "shared" objects passed in via init.
# For things pertaining only to the order, create them in the create method

from .Order import Order


class OrderExample(Order):
    # this example will print information
    def create(self) -> None:
        # here i will get my info
        self.projectInput = self.propertyOperator.createReadOnlyProperty("input", "")

    def run(self, inputVal) -> None:
        print(f"Order input is: {inputVal}")
        self.projectInput.set(inputVal)

    def cleanup(self) -> None:
        print(f"Cleaning up!")

    def getDescription(self) -> str:
        return "displays_input"

    def getName(self) -> str:
        return "order_example"
