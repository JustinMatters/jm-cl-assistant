"""Unit tests for src/tools/sysinfo.py."""

from unittest.mock import MagicMock, patch

from src.tools.sysinfo import _gpu_info, _ollama_models, _ram_info, system_info


class TestRamInfo:
    def test_returns_two_floats(self):
        total, avail = _ram_info()
        assert isinstance(total, float)
        assert isinstance(avail, float)

    def test_psutil_path(self):
        mock_vm = MagicMock()
        mock_vm.total = 16 * 1024**3
        mock_vm.available = 8 * 1024**3
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value = mock_vm
        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            total, avail = _ram_info()
        assert total == 16.0
        assert avail == 8.0

    def test_falls_back_to_zeros_on_failure(self):
        with (
            patch.dict("sys.modules", {"psutil": None}),
            patch("builtins.open", side_effect=OSError),
        ):
            total, avail = _ram_info()
        assert total == 0.0
        assert avail == 0.0


class TestGpuInfo:
    def test_returns_empty_when_torch_missing(self):
        with patch.dict("sys.modules", {"torch": None}):
            result = _gpu_info()
        assert result == []

    def test_returns_empty_when_cuda_unavailable(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = _gpu_info()
        assert result == []

    def test_returns_gpu_info_when_available(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "RTX 3090"
        props = MagicMock()
        props.total_memory = 24 * 1024**3
        mock_torch.cuda.get_device_properties.return_value = props
        mock_torch.cuda.memory_allocated.return_value = 4 * 1024**3
        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = _gpu_info()
        assert len(result) == 1
        assert "RTX 3090" in result[0]
        assert "24.0 GiB" in result[0]


class TestOllamaModels:
    def test_returns_model_names(self):
        m1, m2 = MagicMock(), MagicMock()
        m1.model = "llama3:8b"
        m2.model = "qwen3:1.7b"
        mock_list = MagicMock()
        mock_list.models = [m1, m2]
        with patch("src.tools.sysinfo.ollama.list", return_value=mock_list):
            result = _ollama_models()
        assert result == ["llama3:8b", "qwen3:1.7b"]

    def test_returns_empty_on_error(self):
        with patch(
            "src.tools.sysinfo.ollama.list", side_effect=Exception("offline")
        ):
            result = _ollama_models()
        assert result == []


class TestSystemInfo:
    def _patch_all(
        self,
        ram=(16.0, 8.0),
        gpu=None,
        models=None,
    ):
        if gpu is None:
            gpu = []
        if models is None:
            models = ["qwen3:1.7b"]
        return (
            patch("src.tools.sysinfo._ram_info", return_value=ram),
            patch("src.tools.sysinfo._gpu_info", return_value=gpu),
            patch("src.tools.sysinfo._ollama_models", return_value=models),
        )

    def test_includes_os(self):
        p1, p2, p3 = self._patch_all()
        with p1, p2, p3:
            result = system_info()
        assert "OS:" in result

    def test_includes_cpu(self):
        p1, p2, p3 = self._patch_all()
        with p1, p2, p3:
            result = system_info()
        assert "CPU:" in result

    def test_includes_ram(self):
        p1, p2, p3 = self._patch_all(ram=(16.0, 8.0))
        with p1, p2, p3:
            result = system_info()
        assert "RAM:" in result
        assert "8.0" in result
        assert "16.0" in result

    def test_includes_python_version(self):
        p1, p2, p3 = self._patch_all()
        with p1, p2, p3:
            result = system_info()
        assert "Python:" in result

    def test_includes_ollama_models(self):
        p1, p2, p3 = self._patch_all(models=["qwen3:1.7b"])
        with p1, p2, p3:
            result = system_info()
        assert "qwen3:1.7b" in result

    def test_no_ollama_shows_message(self):
        p1, p2, p3 = self._patch_all(models=[])
        with p1, p2, p3:
            result = system_info()
        assert "none loaded" in result

    def test_gpu_unavailable_shows_message(self):
        p1, p2, p3 = self._patch_all(gpu=[])
        with p1, p2, p3:
            result = system_info()
        assert "GPU: not available" in result

    def test_gpu_shown_when_available(self):
        p1, p2, p3 = self._patch_all(gpu=["GPU 0: RTX 3090 — 24.0 GiB total"])
        with p1, p2, p3:
            result = system_info()
        assert "RTX 3090" in result

    def test_ram_unavailable_shows_message(self):
        p1, p2, p3 = self._patch_all(ram=(0.0, 0.0))
        with p1, p2, p3:
            result = system_info()
        assert "unavailable" in result


class TestGlobalRegistration:
    def test_sysinfo_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "sysinfo" in names

    def test_sysinfo_tier_and_category(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "sysinfo")
        assert tool.router_tier == "sysinfo"
        assert tool.category == "system"
        assert tool.approach == "A"
