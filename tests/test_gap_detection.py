"""
Unit tests for gap detection system.

Tests the DuckDB LAG() window function gap detection, gap analysis,
and validation report storage functionality.
"""

import json
import pytest
import duckdb
from pathlib import Path
from datetime import datetime
import sys
from unittest.mock import Mock, patch, MagicMock

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent / ".claude" / "skills" / "motherduck-pipeline-operations" / "scripts"
sys.path.insert(0, str(scripts_dir))

import detect_gaps


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_validation_db(tmp_path):
    """Temporary validation database for testing."""
    db_path = tmp_path / "test_validation.duckdb"
    original_path = detect_gaps.VALIDATION_DB
    detect_gaps.VALIDATION_DB = db_path
    yield db_path
    detect_gaps.VALIDATION_DB = original_path


@pytest.fixture
def mock_motherduck_conn():
    """Mock MotherDuck connection for testing."""
    conn = duckdb.connect(':memory:')

    # Create test table
    conn.execute("""
        CREATE TABLE ethereum_mainnet_blocks (
            number BIGINT PRIMARY KEY,
            timestamp TIMESTAMP
        )
    """)

    # Set up MotherDuck table reference
    conn.execute("CREATE SCHEMA ethereum_mainnet")
    conn.execute("""
        CREATE VIEW ethereum_mainnet.blocks AS
        SELECT * FROM ethereum_mainnet_blocks
    """)

    yield conn
    conn.close()


def insert_blocks(conn, blocks):
    """Helper to insert test blocks."""
    for block_num in blocks:
        conn.execute(
            "INSERT INTO ethereum_mainnet_blocks VALUES (?, ?)",
            (block_num, datetime(2020, 1, 1, 0, block_num * 12))  # ~12s per block
        )


# =============================================================================
# Gap Detection Tests
# =============================================================================

def test_detect_no_gaps(mock_motherduck_conn):
    """Test gap detection with complete sequence (no gaps)."""
    # Insert continuous sequence: 1000-1100
    insert_blocks(mock_motherduck_conn, range(1000, 1101))

    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert analysis.total_blocks == 101
    assert analysis.expected_blocks == 101
    assert analysis.missing_blocks == 0
    assert len(analysis.gaps) == 0
    assert not analysis.has_gaps
    assert analysis.completeness_pct == 100.0


def test_detect_single_gap(mock_motherduck_conn):
    """Test gap detection with single missing block."""
    # Insert sequence with gap at 1050: 1000-1049, 1051-1100
    blocks = list(range(1000, 1050)) + list(range(1051, 1101))
    insert_blocks(mock_motherduck_conn, blocks)

    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert analysis.total_blocks == 100
    assert analysis.expected_blocks == 101
    assert analysis.missing_blocks == 1
    assert len(analysis.gaps) == 1
    assert analysis.has_gaps

    gap = analysis.gaps[0]
    assert gap.start_block == 1050
    assert gap.end_block == 1050
    assert gap.gap_size == 1


def test_detect_multiple_gaps(mock_motherduck_conn):
    """Test gap detection with multiple gaps."""
    # Insert sequence with 3 gaps:
    # 1000-1010, [gap: 1011-1015], 1016-1020, [gap: 1021-1025], 1026-1030, [gap: 1031-1035], 1036-1040
    blocks = (list(range(1000, 1011)) +
              list(range(1016, 1021)) +
              list(range(1026, 1031)) +
              list(range(1036, 1041)))
    insert_blocks(mock_motherduck_conn, blocks)

    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert analysis.total_blocks == 26
    assert analysis.expected_blocks == 41
    assert analysis.missing_blocks == 15
    assert len(analysis.gaps) == 3
    assert analysis.has_gaps

    # Check gap details
    assert analysis.gaps[0].start_block == 1011
    assert analysis.gaps[0].end_block == 1015
    assert analysis.gaps[0].gap_size == 5

    assert analysis.gaps[1].start_block == 1021
    assert analysis.gaps[1].end_block == 1025
    assert analysis.gaps[1].gap_size == 5

    assert analysis.gaps[2].start_block == 1031
    assert analysis.gaps[2].end_block == 1035
    assert analysis.gaps[2].gap_size == 5


def test_detect_large_gap(mock_motherduck_conn):
    """Test gap detection with large gap."""
    # Insert sequence with large gap: 1000-1010, [gap: 1011-10000], 10001-10100
    blocks = list(range(1000, 1011)) + list(range(10001, 10101))
    insert_blocks(mock_motherduck_conn, blocks)

    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert analysis.total_blocks == 111
    assert analysis.expected_blocks == 9101
    assert analysis.missing_blocks == 8990
    assert len(analysis.gaps) == 1

    gap = analysis.gaps[0]
    assert gap.start_block == 1011
    assert gap.end_block == 10000
    assert gap.gap_size == 8990
    assert analysis.completeness_pct < 2.0  # Very incomplete


def test_gap_at_start(mock_motherduck_conn):
    """Test gap detection when gap is at start of sequence."""
    # Insert sequence starting from block 1005 (gap: 1000-1004 missing)
    insert_blocks(mock_motherduck_conn, range(1005, 1101))

    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert analysis.total_blocks == 96
    assert analysis.expected_blocks == 96  # No gap detected (LAG() only finds internal gaps)
    assert len(analysis.gaps) == 0  # LAG() doesn't detect leading gaps


def test_gap_at_end(mock_motherduck_conn):
    """Test gap detection when gap is at end of sequence."""
    # Insert sequence ending at block 1095 (gap: 1096-1100 missing)
    insert_blocks(mock_motherduck_conn, range(1000, 1096))

    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert analysis.total_blocks == 96
    assert analysis.expected_blocks == 96  # No gap detected (LAG() only finds internal gaps)
    assert len(analysis.gaps) == 0  # LAG() doesn't detect trailing gaps


# =============================================================================
# Gap Analysis Tests
# =============================================================================

def test_gap_analysis_completeness_calculation():
    """Test completeness percentage calculation."""
    analysis = detect_gaps.GapAnalysis(
        total_blocks=9500,
        expected_blocks=10000,
        missing_blocks=500,
        gaps=[],
        detection_timestamp="2025-11-10T00:00:00"
    )

    assert analysis.completeness_pct == 95.0


def test_gap_analysis_has_gaps():
    """Test has_gaps property."""
    analysis_with_gaps = detect_gaps.GapAnalysis(
        total_blocks=9500,
        expected_blocks=10000,
        missing_blocks=500,
        gaps=[detect_gaps.Gap(1000, 1499, 500)],
        detection_timestamp="2025-11-10T00:00:00"
    )
    assert analysis_with_gaps.has_gaps

    analysis_no_gaps = detect_gaps.GapAnalysis(
        total_blocks=10000,
        expected_blocks=10000,
        missing_blocks=0,
        gaps=[],
        detection_timestamp="2025-11-10T00:00:00"
    )
    assert not analysis_no_gaps.has_gaps


# =============================================================================
# Validation Storage Tests
# =============================================================================

def test_validation_storage_creates_table(temp_validation_db):
    """Test that validation storage creates table on first use."""
    analysis = detect_gaps.GapAnalysis(
        total_blocks=10000,
        expected_blocks=10000,
        missing_blocks=0,
        gaps=[],
        detection_timestamp="2025-11-10T00:00:00"
    )

    detect_gaps.store_validation_report(analysis)

    # Verify table exists
    conn = duckdb.connect(str(temp_validation_db))
    tables = conn.execute("SHOW TABLES").fetchall()
    assert ('gap_detection_reports',) in tables
    conn.close()


def test_validation_storage_insert(temp_validation_db):
    """Test storing validation report."""
    gaps = [
        detect_gaps.Gap(1000, 1004, 5, "2020-01-01 00:00:00", "2020-01-01 01:00:00"),
        detect_gaps.Gap(2000, 2009, 10, "2020-01-02 00:00:00", "2020-01-02 02:00:00")
    ]

    analysis = detect_gaps.GapAnalysis(
        total_blocks=9985,
        expected_blocks=10000,
        missing_blocks=15,
        gaps=gaps,
        detection_timestamp="2025-11-10T12:00:00"
    )

    detect_gaps.store_validation_report(analysis)

    # Verify stored data
    conn = duckdb.connect(str(temp_validation_db))
    result = conn.execute("""
        SELECT
            total_blocks,
            expected_blocks,
            missing_blocks,
            completeness_pct,
            num_gaps,
            gap_details
        FROM gap_detection_reports
        WHERE detection_timestamp = '2025-11-10T12:00:00'
    """).fetchone()

    assert result[0] == 9985  # total_blocks
    assert result[1] == 10000  # expected_blocks
    assert result[2] == 15  # missing_blocks
    assert result[3] == pytest.approx(99.85)  # completeness_pct
    assert result[4] == 2  # num_gaps

    gap_details = json.loads(result[5])
    assert len(gap_details) == 2
    assert gap_details[0]["start_block"] == 1000
    assert gap_details[0]["gap_size"] == 5

    conn.close()


def test_validation_storage_upsert(temp_validation_db):
    """Test that storing same timestamp replaces previous record."""
    timestamp = "2025-11-10T12:00:00"

    analysis1 = detect_gaps.GapAnalysis(
        total_blocks=9000,
        expected_blocks=10000,
        missing_blocks=1000,
        gaps=[detect_gaps.Gap(1000, 1999, 1000)],
        detection_timestamp=timestamp
    )
    detect_gaps.store_validation_report(analysis1)

    analysis2 = detect_gaps.GapAnalysis(
        total_blocks=9500,
        expected_blocks=10000,
        missing_blocks=500,
        gaps=[detect_gaps.Gap(1000, 1499, 500)],
        detection_timestamp=timestamp
    )
    detect_gaps.store_validation_report(analysis2)

    # Verify only one record exists with updated values
    conn = duckdb.connect(str(temp_validation_db))
    count = conn.execute("""
        SELECT COUNT(*) FROM gap_detection_reports
        WHERE detection_timestamp = ?
    """, (timestamp,)).fetchone()[0]

    result = conn.execute("""
        SELECT total_blocks, missing_blocks FROM gap_detection_reports
        WHERE detection_timestamp = ?
    """, (timestamp,)).fetchone()

    assert count == 1
    assert result[0] == 9500  # Updated value
    assert result[1] == 500  # Updated value

    conn.close()


# =============================================================================
# Token Retrieval Tests
# =============================================================================

def test_get_motherduck_token_from_env():
    """Test token retrieval from environment variable."""
    with patch.dict('os.environ', {'MOTHERDUCK_TOKEN': 'test_token_123'}):
        token = detect_gaps.get_motherduck_token()
        assert token == 'test_token_123'


def test_get_motherduck_token_from_doppler():
    """Test token retrieval from Doppler when env var not set."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = 'doppler_token_456\n'

    with patch.dict('os.environ', {}, clear=True):
        with patch('subprocess.run', return_value=mock_result):
            token = detect_gaps.get_motherduck_token()
            assert token == 'doppler_token_456'


def test_get_motherduck_token_missing():
    """Test error raised when token not found."""
    mock_result = Mock()
    mock_result.returncode = 1

    with patch.dict('os.environ', {}, clear=True):
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(RuntimeError, match="MOTHERDUCK_TOKEN not found"):
                detect_gaps.get_motherduck_token()


# =============================================================================
# Gap Data Class Tests
# =============================================================================

def test_gap_repr():
    """Test Gap string representation."""
    gap = detect_gaps.Gap(
        start_block=10000,
        end_block=10500,
        gap_size=501
    )

    repr_str = repr(gap)
    assert "10,000" in repr_str
    assert "10,500" in repr_str
    assert "501" in repr_str


def test_gap_with_timestamps():
    """Test Gap with timestamps."""
    gap = detect_gaps.Gap(
        start_block=10000,
        end_block=10500,
        gap_size=501,
        start_timestamp="2020-01-01 00:00:00",
        end_timestamp="2020-01-01 02:00:00"
    )

    assert gap.start_timestamp == "2020-01-01 00:00:00"
    assert gap.end_timestamp == "2020-01-01 02:00:00"


# =============================================================================
# Integration Test
# =============================================================================

def test_end_to_end_gap_detection_with_storage(mock_motherduck_conn, temp_validation_db):
    """Integration test: detect gaps and store validation report."""
    # Create realistic scenario with multiple gaps
    blocks = (list(range(11_560_000, 11_560_100)) +  # 100 blocks
              list(range(11_560_150, 11_560_200)) +  # Gap: 50 blocks
              list(range(11_560_250, 11_560_300)))   # Gap: 50 blocks

    insert_blocks(mock_motherduck_conn, blocks)

    # Detect gaps
    analysis = detect_gaps.detect_gaps(mock_motherduck_conn)

    assert len(analysis.gaps) == 2
    assert analysis.missing_blocks == 100
    assert analysis.total_blocks == 150

    # Store validation report
    detect_gaps.store_validation_report(analysis)

    # Verify stored report
    conn = duckdb.connect(str(temp_validation_db))
    result = conn.execute("""
        SELECT num_gaps, missing_blocks FROM gap_detection_reports
    """).fetchone()

    assert result[0] == 2
    assert result[1] == 100

    conn.close()


# =============================================================================
# Alerting Tests (Mocked)
# =============================================================================

@patch('requests.post')
def test_send_pushover_alert_with_gaps(mock_post):
    """Test Pushover alert sent when gaps detected."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response

    analysis = detect_gaps.GapAnalysis(
        total_blocks=9900,
        expected_blocks=10000,
        missing_blocks=100,
        gaps=[detect_gaps.Gap(5000, 5099, 100)],
        detection_timestamp="2025-11-10T00:00:00"
    )

    with patch.dict('os.environ', {'PUSHOVER_TOKEN': 'test', 'PUSHOVER_USER': 'user'}):
        detect_gaps.send_pushover_alert(analysis)

    assert mock_post.called
    call_data = mock_post.call_args[1]['data']
    assert '100' in call_data['message']  # Missing blocks count
    assert call_data['priority'] == 1  # High priority


@patch('requests.post')
def test_send_pushover_alert_no_gaps(mock_post):
    """Test Pushover alert NOT sent when no gaps."""
    analysis = detect_gaps.GapAnalysis(
        total_blocks=10000,
        expected_blocks=10000,
        missing_blocks=0,
        gaps=[],
        detection_timestamp="2025-11-10T00:00:00"
    )

    with patch.dict('os.environ', {'PUSHOVER_TOKEN': 'test', 'PUSHOVER_USER': 'user'}):
        detect_gaps.send_pushover_alert(analysis)

    assert not mock_post.called


@patch('requests.post')
@patch('requests.get')
def test_ping_healthchecks_with_gaps(mock_get, mock_post):
    """Test Healthchecks.io ping with /fail when gaps detected."""
    # Mock check lookup
    mock_get_response = Mock()
    mock_get_response.json.return_value = {
        "checks": [{
            "name": "eth-gap-detection",
            "ping_url": "https://hc-ping.com/test-uuid"
        }]
    }
    mock_get_response.raise_for_status = Mock()
    mock_get.return_value = mock_get_response

    # Mock ping
    mock_ping_response = Mock()
    mock_ping_response.raise_for_status = Mock()
    mock_post.return_value = mock_ping_response

    analysis = detect_gaps.GapAnalysis(
        total_blocks=9900,
        expected_blocks=10000,
        missing_blocks=100,
        gaps=[detect_gaps.Gap(5000, 5099, 100)],
        detection_timestamp="2025-11-10T00:00:00"
    )

    with patch.dict('os.environ', {'HEALTHCHECKS_API_KEY': 'test_key'}):
        detect_gaps.ping_healthchecks(analysis)

    # Verify /fail endpoint called
    assert mock_post.called
    ping_url = mock_post.call_args[0][0]
    assert ping_url.endswith('/fail')
