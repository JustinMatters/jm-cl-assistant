import pytest

router_module = pytest.importorskip("src.router")
OllamaRouter = router_module.OllamaRouter

TRIVIAL_QUERIES = [
    "hi",
    "what colour is the sky",
    "What is the capital of France?",
]

SIMPLE_QUERIES = [
    "What is 2+2?",
    "What is 15% of 200?",
    "How do you say hello in Spanish?",
]

COMPLEX_SONNET_QUERIES = [
    "Explain the causes and consequences of the French Revolution.",
    "Write a short essay comparing Keynesian and Austrian economics.",
    "Summarise the key arguments for and against universal basic income.",
]

COMPLEX_OPUS_QUERIES = [
    (
        "Design a distributed system architecture for a real-time global "
        "financial trading platform handling 10 million transactions "
        "per second."
    ),
    (
        "Provide a rigorous mathematical proof of the Riemann hypothesis "
        "and discuss its implications for prime number distribution."
    ),
    (
        "Write a full research proposal for a novel cancer immunotherapy "
        "approach, including methodology, controls, and statistical analysis."
    ),
]

VALID_CLASSIFICATIONS = {
    "trivial_ollama",
    "simple_ollama",
    "complex_sonnet",
    "complex_opus",
    "maths",
}

MATHS_QUERIES = [
    "what is 2 + 2?",
    "calculate sqrt(144)",
    "15% of 200",
    "2 ** 10",
]


class TestOllamaRouterClassify:
    def test_returns_valid_classification_for_trivial_query(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "trivial_ollama"}}
        router = OllamaRouter()
        result = router.classify(TRIVIAL_QUERIES[0])
        assert result in VALID_CLASSIFICATIONS

    def test_trivial_query_classified_as_trivial_ollama(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "trivial_ollama"}}
        router = OllamaRouter()
        result = router.classify(TRIVIAL_QUERIES[0])
        assert result == "trivial_ollama"

    def test_returns_valid_classification_for_simple_query(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple_ollama"}}
        router = OllamaRouter()
        result = router.classify(SIMPLE_QUERIES[0])
        assert result in VALID_CLASSIFICATIONS

    def test_simple_query_classified_as_simple_ollama(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple_ollama"}}
        router = OllamaRouter()
        result = router.classify(SIMPLE_QUERIES[0])
        assert result == "simple_ollama"

    def test_moderate_query_classified_as_complex_sonnet(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "complex_sonnet"}}
        router = OllamaRouter()
        result = router.classify(COMPLEX_SONNET_QUERIES[0])
        assert result == "complex_sonnet"

    def test_hard_query_classified_as_complex_opus(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "complex_opus"}}
        router = OllamaRouter()
        result = router.classify(COMPLEX_OPUS_QUERIES[0])
        assert result == "complex_opus"

    def test_empty_input_returns_valid_classification(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "trivial_ollama"}}
        router = OllamaRouter()
        result = router.classify("")
        assert result in VALID_CLASSIFICATIONS

    def test_non_english_input_returns_valid_classification(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple_ollama"}}
        router = OllamaRouter()
        result = router.classify("Quelle est la capitale de la France?")
        assert result in VALID_CLASSIFICATIONS

    def test_unparseable_model_output_falls_back_to_trivial_ollama(
        self, mocker
    ):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {
            "message": {"content": "I am unable to determine this."}
        }
        router = OllamaRouter()
        result = router.classify(SIMPLE_QUERIES[0])
        assert result == "trivial_ollama"

    def test_whitespace_padded_response_is_handled(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {
            "message": {"content": "  complex_sonnet  \n"}
        }
        router = OllamaRouter()
        result = router.classify(COMPLEX_SONNET_QUERIES[0])
        assert result == "complex_sonnet"

    def test_ollama_client_is_called_once_per_classify(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "trivial_ollama"}}
        router = OllamaRouter()
        router.classify(SIMPLE_QUERIES[0])
        mock_client.assert_called_once()

    @pytest.mark.parametrize("query", SIMPLE_QUERIES)
    def test_multiple_simple_queries_all_return_valid(self, mocker, query):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple_ollama"}}
        router = OllamaRouter()
        result = router.classify(query)
        assert result in VALID_CLASSIFICATIONS


class TestMathsClassification:
    def test_maths_query_classified_as_maths(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "maths"}}
        router = OllamaRouter()
        result = router.classify("what is 2 + 2?")
        assert result == "maths"

    def test_maths_is_a_valid_classification(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "maths"}}
        router = OllamaRouter()
        result = router.classify(MATHS_QUERIES[0])
        assert result in VALID_CLASSIFICATIONS

    @pytest.mark.parametrize("query", MATHS_QUERIES)
    def test_multiple_maths_queries_all_return_valid(self, mocker, query):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "maths"}}
        router = OllamaRouter()
        result = router.classify(query)
        assert result in VALID_CLASSIFICATIONS


class TestOllamaRouterErrorHandling:
    def test_connection_error_falls_back_to_trivial_ollama(self, mocker):
        mocker.patch(
            "src.router.ollama.chat",
            side_effect=ConnectionError("Ollama not running"),
        )
        router = OllamaRouter()
        result = router.classify("hi")
        assert result == "trivial_ollama"

    def test_response_error_falls_back_to_trivial_ollama(self, mocker):
        mocker.patch(
            "src.router.ollama.chat",
            side_effect=Exception("ResponseError: model not found"),
        )
        router = OllamaRouter()
        result = router.classify("hi")
        assert result == "trivial_ollama"

    def test_generic_exception_falls_back_to_trivial_ollama(self, mocker):
        mocker.patch(
            "src.router.ollama.chat",
            side_effect=RuntimeError("unexpected failure"),
        )
        router = OllamaRouter()
        result = router.classify("hi")
        assert result == "trivial_ollama"

    def test_connection_error_emits_warning(self, mocker):
        mocker.patch(
            "src.router.ollama.chat",
            side_effect=ConnectionError("Ollama not running"),
        )
        router = OllamaRouter()
        with pytest.warns(UserWarning, match="Ollama router failed"):
            router.classify("hi")
