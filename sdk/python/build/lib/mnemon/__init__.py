from .client import MnemonClient, TenantStatus, QueryResult, MnemonException

Client = MnemonClient

__all__ = ["Client", "MnemonClient", "TenantStatus", "QueryResult", "MnemonException"]
__version__ = "1.2.0"

