# pip install deepeval
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

def test_answer_relevancy():
    test_case = LLMTestCase(
        input="Quel est le taux de TVA en France ?",
        actual_output="Le taux normal de TVA en France est de 20%.",
    )
    metric = AnswerRelevancyMetric(threshold=0.7)
    metric.measure(test_case)
    assert metric.is_successful()
