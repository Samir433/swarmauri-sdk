import pytest
from swarmauri.standard.tools.concrete.CalculatorTool import CalculatorTool

@pytest.mark.unit
def test_ubc_resource():
    def test():
        tool = CalculatorTool()
        assert tool.resource == 'Tool'
    test()

@pytest.mark.unit
def test_initialization():
    def test():
        tool = CalculatorTool()
        assert type(tool.swm_path) == str
        assert type(tool.id) == str

    test()


@pytest.mark.unit
def test_call():
    def test():
        tool = CalculatorTool()
        assert tool('add', 2, 3) == str(5)
        assert tool('subtract', 17, 2) == str(15)
        assert tool('multiply', 100, 5) == str(500)
        assert tool('divide', 100, 2) == str(50.0)
    test()