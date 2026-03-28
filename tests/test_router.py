import pytest

router_module = pytest.importorskip("src.router")
OllamaRouter = router_module.OllamaRouter

SIMPLE_QUERIES = [
    "What is the capital of France?",
    "What time is it?",
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

VALID_CLASSIFICATIONS = {"simple", "complex_sonnet", "complex_opus"}


class TestOllamaRouterClassify:
    def test_returns_valid_classification_for_simple_query(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple"}}
        router = OllamaRouter()
        result = router.classify(SIMPLE_QUERIES[0])
        assert result in VALID_CLASSIFICATIONS

    def test_simple_query_classified_as_simple(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple"}}
        router = OllamaRouter()
        result = router.classify(SIMPLE_QUERIES[0])
        assert result == "simple"

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
        mock_client.return_value = {"message": {"content": "simple"}}
        router = OllamaRouter()
        result = router.classify("")
        assert result in VALID_CLASSIFICATIONS

    def test_non_english_input_returns_valid_classification(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple"}}
        router = OllamaRouter()
        result = router.classify("Quelle est la capitale de la France?")
        assert result in VALID_CLASSIFICATIONS

    def test_unparseable_model_output_falls_back_to_simple(self, mocker):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {
            "message": {"content": "I am unable to determine this."}
        }
        router = OllamaRouter()
        result = router.classify(SIMPLE_QUERIES[0])
        assert result in VALID_CLASSIFICATIONS

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
        mock_client.return_value = {"message": {"content": "simple"}}
        router = OllamaRouter()
        router.classify(SIMPLE_QUERIES[0])
        mock_client.assert_called_once()

    @pytest.mark.parametrize("query", SIMPLE_QUERIES)
    def test_multiple_simple_queries_all_return_valid(self, mocker, query):
        mock_client = mocker.patch("src.router.ollama.chat")
        mock_client.return_value = {"message": {"content": "simple"}}
        router = OllamaRouter()
        result = router.classify(query)
        assert result in VALID_CLASSIFICATIONS
