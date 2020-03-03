internal data class UsageInfo(val usageCount: Int, val lastUsedTimestamp: Long)

// send from idea
internal data class TipsRequest(
  val tips: List<String>,
  val usageInfo: Map<String, UsageInfo>,
  val ideName: String,
  val bucket: Int
)

// receive in idea
internal data class ServerRecommendation(
  val showingOrder: List<String>,
  val usedAlgorithm: String
)