import React, { useState, useEffect } from "react";
import {
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  FileText,
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  HelpCircle,
  TrendingDown,
  Globe,
  MapPin,
  Layers,
  ArrowRight,
  Download,
  Copy,
} from "lucide-react";

interface GDBItem {
  gdb_id: string;
  sample_query: string;
  sample_answer: string;
  crop: string;
  domain: string;
  state: string;
  total_responses: number;
  positive_count: number;
  negative_count: number;
  helpfulness_rate: number;
  is_flagged: boolean;
}

interface Breakdown {
  category: string;
  total_responses: number;
  positive_count: number;
  negative_count: number;
  helpfulness_rate: number;
}

const DEFAULT_GDB_ITEMS: GDBItem[] = [
  {
    gdb_id: "gdb_entry_108",
    crop: "Soybean",
    domain: "Weed Management",
    state: "Maharashtra",
    sample_query: "सोयाबीन पिकातील तण नियंत्रणासाठी कोणते तणनाशक वापरावे?",
    sample_answer: "सोयाबीनमध्ये पेरणीनंतर 15 ते 20 दिवसांनी इमेझाथापीर 10% SL 400 मिली प्रति एकर फवारावे.",
    total_responses: 12,
    positive_count: 4,
    negative_count: 8,
    helpfulness_rate: 0.333,
    is_flagged: true,
  },
  {
    gdb_id: "gdb_entry_101",
    crop: "Cotton",
    domain: "Plant Protection",
    state: "Telangana",
    sample_query: "పత్తిలో గులాబీ రంగు పురుగు నివారణ ఏమిటి?",
    sample_answer: "గులాబీ రంగు పురుగు నివారణకు ప్రొఫెనోఫాస్ 50% EC 2 మి.లీ లేదా ఇమామెక్టిన్ బెంజోయేట్ 5% SG 0.4 గ్రాములు ఒక లీటరు నీటికి కలిపి పిచికారీ చేయాలి.",
    total_responses: 15,
    positive_count: 7,
    negative_count: 8,
    helpfulness_rate: 0.467,
    is_flagged: true,
  },
  {
    gdb_id: "gdb_entry_103",
    crop: "Chilli",
    domain: "Plant Protection",
    state: "Andhra Pradesh",
    sample_query: "మిరపలో ఆకు ముడత నివారణ చర్యలు ఏమిటి?",
    sample_answer: "తామర పురుగుల వల్ల వచ్చే ఆకు ముడత నివారణకు స్పైనోసాడ్ 45% SC 0.3 మి.లీ లేదా ఫిప్రోనిల్ 5% SC 2 మి.లీ లీటరు నీటికి కలిపి పిచికారీ చేయాలి.",
    total_responses: 14,
    positive_count: 7,
    negative_count: 7,
    helpfulness_rate: 0.500,
    is_flagged: true,
  },
  {
    gdb_id: "gdb_entry_105",
    crop: "Sugarcane",
    domain: "Cultural Practices",
    state: "Maharashtra",
    sample_query: "ऊस पिकात लाल कुजव्या रोगाचा प्रादुर्भाव कसा रोखावा?",
    sample_answer: "लाल कुजव्या रोगासाठी निरोगी बेणे वापरावे, ट्रायकोडरमा विरिडी 2.5 किलो शेणखतात मिसळून एकरी द्यावे.",
    total_responses: 11,
    positive_count: 8,
    negative_count: 3,
    helpfulness_rate: 0.727,
    is_flagged: false,
  },
  {
    gdb_id: "gdb_entry_102",
    crop: "Paddy",
    domain: "Plant Protection",
    state: "Telangana",
    sample_query: "వరిలో కాండం తొలుచు పురుగు లక్షణాలు మరియు నివారణ?",
    sample_answer: "వరిలో కాండం తొలుచు పురుగు ఆశించినప్పుడు మొవ్వు ఎండిపోయి తెల్లకంకులు వస్తాయి. కార్టాప్ హైడ్రోక్లోరైడ్ 50% SP 2 గ్రాములు లీటరు నీటికి కలపాలి.",
    total_responses: 20,
    positive_count: 17,
    negative_count: 3,
    helpfulness_rate: 0.850,
    is_flagged: false,
  },
  {
    gdb_id: "gdb_entry_107",
    crop: "Maize",
    domain: "Fertilizer Management",
    state: "Madhya Pradesh",
    sample_query: "मक्के की फसल में यूरिया की सही मात्रा और देने का समय क्या है?",
    sample_answer: "मक्के में कुल यूरिया को तीन भागों में दें: एक तिहाई बुवाई के समय, एक तिहाई घुटने की ऊंचाई पर और शेष एक तिहाई नर मंजरी आने पर डालें।",
    total_responses: 16,
    positive_count: 14,
    negative_count: 2,
    helpfulness_rate: 0.875,
    is_flagged: false,
  },
  {
    gdb_id: "gdb_entry_106",
    crop: "Tomato",
    domain: "Nutrient Management",
    state: "Karnataka",
    sample_query: "ಟೊಮೆಟೊ ಹಣ್ಣುಗಳಲ್ಲಿ ಕ್ಯಾಲ್ಸಿಯಂ ಕೊರತೆ ತಡೆಯುವುದು ಹೇಗೆ?",
    sample_answer: "ಕ್ಯಾಲ್ಸಿಯಂ ನೈಟ್ರೇಟ್ 5 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಹೂ ಬಿಡುವ ಮತ್ತು ಕಾಯಿ ಕಟ್ಟುವ ಹಂತದಲ್ಲಿ ಸಿಂಪಡಿಸಿ.",
    total_responses: 18,
    positive_count: 16,
    negative_count: 2,
    helpfulness_rate: 0.889,
    is_flagged: false,
  },
  {
    gdb_id: "gdb_entry_109",
    crop: "Groundnut",
    domain: "Plant Protection",
    state: "Andhra Pradesh",
    sample_query: "వేరుశనగలో తిక్క తెగులు నివారణ మందులు?",
    sample_answer: "తిక్క తెగులు నివారణకు కార్బెండజిమ్ 12% + మాంకోజెబ్ 63% WP 2 గ్రాములు లీటరు నీటికి కలిపి 15 రోజుల వ్యవధిలో రెండు సార్లు పిచికారీ చేయాలి.",
    total_responses: 20,
    positive_count: 18,
    negative_count: 2,
    helpfulness_rate: 0.900,
    is_flagged: false,
  },
  {
    gdb_id: "gdb_entry_104",
    crop: "Wheat",
    domain: "Disease Management",
    state: "Punjab",
    sample_query: "गेहूं में पीला रतुआ के लक्षण और उपचार क्या है?",
    sample_answer: "पीला रतुआ में पत्तियों पर पीले रंग की धारियाँ बनती हैं। प्रोपिकोनाजोल 25% EC का 1 मिली प्रति लीटर पानी में मिलाकर तुरंत छिड़काव करें।",
    total_responses: 25,
    positive_count: 24,
    negative_count: 1,
    helpfulness_rate: 0.960,
    is_flagged: false,
  },
];

const DEFAULT_DOMAINS: Breakdown[] = [
  { category: "Disease Management", total_responses: 25, positive_count: 24, negative_count: 1, helpfulness_rate: 0.96 },
  { category: "Nutrient Management", total_responses: 18, positive_count: 16, negative_count: 2, helpfulness_rate: 0.889 },
  { category: "Fertilizer Management", total_responses: 16, positive_count: 14, negative_count: 2, helpfulness_rate: 0.875 },
  { category: "Cultural Practices", total_responses: 11, positive_count: 8, negative_count: 3, helpfulness_rate: 0.727 },
  { category: "Plant Protection", total_responses: 69, positive_count: 49, negative_count: 20, helpfulness_rate: 0.71 },
  { category: "Weed Management", total_responses: 12, positive_count: 4, negative_count: 8, helpfulness_rate: 0.333 },
];

const DEFAULT_LANGUAGES: Breakdown[] = [
  { category: "HI", total_responses: 41, positive_count: 38, negative_count: 3, helpfulness_rate: 0.927 },
  { category: "KN", total_responses: 18, positive_count: 16, negative_count: 2, helpfulness_rate: 0.889 },
  { category: "TE", total_responses: 69, positive_count: 49, negative_count: 20, helpfulness_rate: 0.71 },
  { category: "MR", total_responses: 23, positive_count: 12, negative_count: 11, helpfulness_rate: 0.522 },
];

const DEFAULT_STATES: Breakdown[] = [
  { category: "Punjab", total_responses: 25, positive_count: 24, negative_count: 1, helpfulness_rate: 0.96 },
  { category: "Karnataka", total_responses: 18, positive_count: 16, negative_count: 2, helpfulness_rate: 0.889 },
  { category: "Madhya Pradesh", total_responses: 16, positive_count: 14, negative_count: 2, helpfulness_rate: 0.875 },
  { category: "Andhra Pradesh", total_responses: 34, positive_count: 25, negative_count: 9, helpfulness_rate: 0.735 },
  { category: "Telangana", total_responses: 35, positive_count: 24, negative_count: 11, helpfulness_rate: 0.686 },
  { category: "Maharashtra", total_responses: 23, positive_count: 12, negative_count: 11, helpfulness_rate: 0.522 },
];

export function FarmerFeedbackDashboard() {
  const [activeTab, setActiveTab] = useState<"gdb" | "domain" | "regional" | "flagged" | "digest">("gdb");
  const [searchTerm, setSearchTerm] = useState("");
  const [domainFilter, setDomainFilter] = useState("all");
  const [minResponsesThreshold, setMinResponsesThreshold] = useState(10);
  const [minHelpfulThreshold, setMinHelpfulThreshold] = useState(60);
  const [copied, setCopied] = useState(false);
  const [items, setItems] = useState<GDBItem[]>(DEFAULT_GDB_ITEMS);

  // Summary Metrics
  const totalFeedbacks = items.reduce((acc, curr) => acc + curr.total_responses, 0);
  const totalPositive = items.reduce((acc, curr) => acc + curr.positive_count, 0);
  const totalNegative = items.reduce((acc, curr) => acc + curr.negative_count, 0);
  const overallRate = totalFeedbacks > 0 ? Math.round((totalPositive / totalFeedbacks) * 100) : 0;
  const flaggedCount = items.filter((i) => i.is_flagged).length;

  const filteredItems = items.filter((item) => {
    const matchSearch =
      item.gdb_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.sample_query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.crop.toLowerCase().includes(searchTerm.toLowerCase());
    const matchDomain = domainFilter === "all" || item.domain === domainFilter;
    return matchSearch && matchDomain;
  });

  const handleManualFlag = (gdbId: string) => {
    setItems((prev) =>
      prev.map((i) => (i.gdb_id === gdbId ? { ...i, is_flagged: !i.is_flagged } : i))
    );
  };

  const runFlagging = () => {
    const thresholdDec = minHelpfulThreshold / 100;
    setItems((prev) =>
      prev.map((i) => ({
        ...i,
        is_flagged: i.total_responses >= minResponsesThreshold && i.helpfulness_rate < thresholdDec,
      }))
    );
    alert(`Flagging pipeline ran! Evaluated threshold: < ${minHelpfulThreshold}% across ${minResponsesThreshold}+ feedbacks.`);
  };

  const copyDigest = () => {
    navigator.clipboard.writeText(
      `# AjraSakha Weekly Digest: Farmer Feedback Loop\nOverall Helpfulness: ${overallRate}%\nTotal Feedbacks: ${totalFeedbacks}\nFlagged Entries: ${flaggedCount}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-semibold">
              WhatsApp Feedback Loop
            </span>
            <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded-full font-semibold">
              Project 5
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 mt-1">
            Farmer Answer Feedback Dashboard
          </h1>
          <p className="text-sm text-gray-500">
            Real-time farmer helpfulness signals from WhatsApp linked directly to Golden Database (GDB) entries.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("digest")}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 shadow-sm"
          >
            <FileText className="w-4 h-4 text-emerald-600" />
            Weekly Digest
          </button>
          <button
            onClick={runFlagging}
            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 shadow-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Run Auto-Flagging
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Feedbacks */}
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Total Farmer Replies</span>
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-gray-900">{totalFeedbacks}</span>
            <span className="text-xs text-gray-500 ml-2">via WhatsApp Bot</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">100% captured after delivery</div>
        </div>

        {/* Overall Helpfulness */}
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Helpfulness Score</span>
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <ThumbsUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-emerald-600">{overallRate}%</span>
            <span className="text-xs text-gray-500">({totalPositive} Yes / {totalNegative} No)</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 mt-3">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${overallRate}%` }} />
          </div>
        </div>

        {/* Unhelpful / Negative */}
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Unhelpful Responses</span>
            <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
              <ThumbsDown className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-amber-600">{totalNegative}</span>
            <span className="text-xs text-gray-500 ml-2">({Math.round((totalNegative / totalFeedbacks) * 100)}%)</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">Reply "2 for No" captured</div>
        </div>

        {/* Flagged for Re-Review */}
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Flagged for Re-Review</span>
            <div className="p-2 bg-rose-50 rounded-lg text-rose-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-rose-600">{flaggedCount}</span>
            <span className="text-xs text-rose-600 font-medium ml-2">GDB Entries</span>
          </div>
          <div className="mt-2 text-xs text-gray-500">&lt; {minHelpfulThreshold}% helpfulness threshold</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("gdb")}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === "gdb"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <Layers className="w-4 h-4" />
            GDB Entries ({items.length})
          </button>
          <button
            onClick={() => setActiveTab("domain")}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === "domain"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <TrendingDown className="w-4 h-4" />
            Domain Performance
          </button>
          <button
            onClick={() => setActiveTab("regional")}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === "regional"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <Globe className="w-4 h-4" />
            Language & State Breakdown
          </button>
          <button
            onClick={() => setActiveTab("flagged")}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === "flagged"
                ? "border-rose-600 text-rose-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            Flagged Re-Review Queue ({flaggedCount})
          </button>
          <button
            onClick={() => setActiveTab("digest")}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
              activeTab === "digest"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <FileText className="w-4 h-4" />
            Agri Team Weekly Digest
          </button>
        </nav>
      </div>

      {/* TAB 1: GDB Entry Helpfulness Table */}
      {activeTab === "gdb" && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search GDB ID, Question, Crop..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={domainFilter}
                onChange={(e) => setDomainFilter(e.target.value)}
                className="border border-gray-300 rounded-lg text-sm px-3 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="all">All Domains</option>
                <option value="Plant Protection">Plant Protection</option>
                <option value="Disease Management">Disease Management</option>
                <option value="Nutrient Management">Nutrient Management</option>
                <option value="Fertilizer Management">Fertilizer Management</option>
                <option value="Weed Management">Weed Management</option>
                <option value="Cultural Practices">Cultural Practices</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">GDB ID & Crop</th>
                  <th className="px-4 py-3">Farmer Query & Answer</th>
                  <th className="px-4 py-3">Domain & State</th>
                  <th className="px-4 py-3 text-center">Replies</th>
                  <th className="px-4 py-3 text-center">Helpful %</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredItems.map((item) => {
                  const pct = Math.round(item.helpfulness_rate * 100);
                  const isLow = pct < 60;
                  return (
                    <tr key={item.gdb_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 align-top whitespace-nowrap">
                        <span className="font-mono text-xs font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                          {item.gdb_id}
                        </span>
                        <div className="font-medium text-gray-900 mt-1">{item.crop}</div>
                      </td>
                      <td className="px-4 py-3 align-top max-w-md">
                        <div className="font-medium text-gray-900">{item.sample_query}</div>
                        <div className="text-xs text-gray-500 mt-1 line-clamp-2">{item.sample_answer}</div>
                      </td>
                      <td className="px-4 py-3 align-top whitespace-nowrap">
                        <div className="text-gray-900">{item.domain}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                          <MapPin className="w-3 h-3 text-gray-400" />
                          {item.state}
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top text-center whitespace-nowrap">
                        <span className="font-semibold text-gray-900">{item.total_responses}</span>
                        <div className="text-xs text-gray-400">
                          ({item.positive_count}Y / {item.negative_count}N)
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top text-center whitespace-nowrap">
                        <span
                          className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold ${
                            isLow ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"
                          }`}
                        >
                          {pct}%
                        </span>
                      </td>
                      <td className="px-4 py-3 align-top text-center whitespace-nowrap">
                        {item.is_flagged ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            <AlertTriangle className="w-3 h-3" />
                            Flagged for Review
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-50 text-gray-600 border border-gray-200">
                            <CheckCircle className="w-3 h-3 text-emerald-500" />
                            Active (Good)
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top text-right whitespace-nowrap">
                        <button
                          onClick={() => handleManualFlag(item.gdb_id)}
                          className={`text-xs px-2.5 py-1 rounded border font-medium ${
                            item.is_flagged
                              ? "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                              : "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100"
                          }`}
                        >
                          {item.is_flagged ? "Unflag" : "Send to Reviewer"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: Domain Breakdown */}
      {activeTab === "domain" && (
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Helpfulness by Agricultural Domain</h2>
            <p className="text-xs text-gray-500 mb-6">
              Compare answer quality across agricultural domains to identify which subject areas struggle most.
            </p>
            <div className="space-y-4">
              {DEFAULT_DOMAINS.map((dom) => {
                const pct = Math.round(dom.helpfulness_rate * 100);
                const isUnderperforming = pct < 60;
                return (
                  <div key={dom.category} className="border-b pb-4 last:border-b-0">
                    <div className="flex justify-between items-center mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-800 text-sm">{dom.category}</span>
                        {isUnderperforming && (
                          <span className="text-[10px] bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded font-bold uppercase">
                            Attention Needed
                          </span>
                        )}
                      </div>
                      <div className="text-sm font-bold">
                        <span className={isUnderperforming ? "text-rose-600" : "text-emerald-600"}>{pct}%</span>
                        <span className="text-xs font-normal text-gray-500 ml-2">
                          ({dom.positive_count} / {dom.total_responses} helpful)
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full ${isUnderperforming ? "bg-rose-500" : "bg-emerald-500"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Language & State Breakdown */}
      {activeTab === "regional" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Language Breakdown */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Globe className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-bold text-gray-900">Performance by Language</h2>
            </div>
            <p className="text-xs text-gray-500 mb-5">Identify dialect or translation clarity gaps.</p>
            <div className="space-y-4">
              {DEFAULT_LANGUAGES.map((lang) => {
                const pct = Math.round(lang.helpfulness_rate * 100);
                return (
                  <div key={lang.category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-gray-700">{lang.category}</span>
                      <span className="font-bold text-gray-900">
                        {pct}% ({lang.total_responses} responses)
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* State Breakdown */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <MapPin className="w-5 h-5 text-emerald-600" />
              <h2 className="text-lg font-bold text-gray-900">Performance by State</h2>
            </div>
            <p className="text-xs text-gray-500 mb-5">Detect regional agricultural relevance issues.</p>
            <div className="space-y-4">
              {DEFAULT_STATES.map((st) => {
                const pct = Math.round(st.helpfulness_rate * 100);
                return (
                  <div key={st.category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-gray-700">{st.category}</span>
                      <span className="font-bold text-gray-900">
                        {pct}% ({st.total_responses} responses)
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Automated Flagging Queue */}
      {activeTab === "flagged" && (
        <div className="space-y-5">
          {/* Threshold Config Card */}
          <div className="bg-amber-50 border border-amber-200 p-5 rounded-xl">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <h3 className="font-bold text-amber-900 text-sm">Automated Re-Review Threshold Settings</h3>
            </div>
            <p className="text-xs text-amber-800 mt-1">
              Any GDB answer receiving at least <strong>{minResponsesThreshold}+ farmer feedback replies</strong> with a
              helpfulness score below <strong>{minHelpfulThreshold}%</strong> is automatically sent back to the
              human expert reviewer pipeline.
            </p>
            <div className="mt-4 flex flex-wrap gap-4 items-center">
              <div>
                <label className="text-xs text-amber-900 font-medium block">Min Responses:</label>
                <input
                  type="number"
                  value={minResponsesThreshold}
                  onChange={(e) => setMinResponsesThreshold(Number(e.target.value))}
                  className="mt-1 w-24 px-2 py-1 border rounded bg-white text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-amber-900 font-medium block">Min Helpful %:</label>
                <input
                  type="number"
                  value={minHelpfulThreshold}
                  onChange={(e) => setMinHelpfulThreshold(Number(e.target.value))}
                  className="mt-1 w-24 px-2 py-1 border rounded bg-white text-sm"
                />
              </div>
              <button
                onClick={runFlagging}
                className="mt-4 px-3 py-1.5 bg-amber-600 text-white rounded text-sm font-semibold hover:bg-amber-700"
              >
                Apply & Evaluate Pipeline
              </button>
            </div>
          </div>

          {/* Flagged Items List */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
              <span className="font-bold text-gray-800 text-sm">
                Active Flagged Queue ({flaggedCount} entries requiring review)
              </span>
              <span className="text-xs text-gray-500">Connected to Reviewer Desk</span>
            </div>
            <div className="divide-y divide-gray-100">
              {items
                .filter((i) => i.is_flagged)
                .map((flagged) => (
                  <div key={flagged.gdb_id} className="p-4 hover:bg-gray-50 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold bg-rose-100 text-rose-800 px-2 py-0.5 rounded">
                          {flagged.gdb_id}
                        </span>
                        <span className="text-sm font-semibold text-gray-900">{flagged.crop}</span>
                        <span className="text-xs text-gray-500">• {flagged.domain}</span>
                        <span className="text-xs text-gray-500">• {flagged.state}</span>
                      </div>
                      <span className="text-xs font-bold text-rose-600 bg-rose-50 border border-rose-200 px-2.5 py-0.5 rounded-full">
                        {Math.round(flagged.helpfulness_rate * 100)}% Positive ({flagged.positive_count}/{flagged.total_responses})
                      </span>
                    </div>
                    <div className="text-sm font-medium text-gray-800">{flagged.sample_query}</div>
                    <div className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded border border-gray-100">
                      {flagged.sample_answer}
                    </div>
                    <div className="flex justify-between items-center pt-2">
                      <span className="text-xs text-rose-600 font-medium flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Flagged Reason: Less than {minHelpfulThreshold}% positive across {flagged.total_responses} responses.
                      </span>
                      <a
                        href="/coordinator"
                        className="text-xs text-emerald-600 font-semibold hover:underline flex items-center gap-1"
                      >
                        Open in Reviewer Desk
                        <ArrowRight className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: Agri Team Weekly Digest */}
      {activeTab === "digest" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b pb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">🌾 Agri Team Weekly Digest</h2>
              <p className="text-xs text-gray-500">
                Official farmer feedback digest for agricultural specialists to prioritize knowledge base updates.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={copyDigest}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs border rounded-lg hover:bg-gray-50 text-gray-700"
              >
                <Copy className="w-3.5 h-3.5" />
                {copied ? "Copied!" : "Copy Summary"}
              </button>
            </div>
          </div>

          <div className="space-y-4 text-sm text-gray-800">
            <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100">
              <h4 className="font-bold text-emerald-900 text-sm mb-1">Executive Summary (Week 1)</h4>
              <p className="text-xs text-emerald-800">
                Over the past 7 days, AjraSakha captured <strong>{totalFeedbacks} verified farmer feedback responses</strong> via the WhatsApp follow-up prompt. 
                Overall helpfulness is <strong>{overallRate}%</strong>. A total of <strong>{flaggedCount} GDB entries</strong> breached the helpfulness threshold and were queued for human expert review.
              </p>
            </div>

            <div>
              <h4 className="font-bold text-gray-900 mb-2">🚨 Priority Fixes (Lowest-Rated Answers)</h4>
              <ul className="list-disc pl-5 space-y-1 text-xs text-gray-600">
                <li>
                  <strong>gdb_entry_108 (Soybean - Weed Management, 33.3%):</strong> Dosage instruction is confusing farmers during post-emergence spray.
                </li>
                <li>
                  <strong>gdb_entry_101 (Cotton - Plant Protection, 46.7%):</strong> Chemical names (Profenofos, Emamectin) lack commonly recognized brand names in Telangana.
                </li>
                <li>
                  <strong>gdb_entry_103 (Chilli - Plant Protection, 50.0%):</strong> Missing precise per-acre water gallon recommendation for thrips control.
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-gray-900 mb-2">🎯 Recommended Actions for Agri Team</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="p-3 border rounded-lg bg-gray-50">
                  <div className="font-bold text-xs text-gray-900">1. Simplify Technical Terms</div>
                  <div className="text-[11px] text-gray-500 mt-1">
                    Provide trade names alongside active chemical ingredients to improve farmer trust and recognition.
                  </div>
                </div>
                <div className="p-3 border rounded-lg bg-gray-50">
                  <div className="font-bold text-xs text-gray-900">2. Keep Steps Under 4 Bullets</div>
                  <div className="text-[11px] text-gray-500 mt-1">
                    WhatsApp users disengage with paragraphs. Prioritize immediate actionable guidance.
                  </div>
                </div>
                <div className="p-3 border rounded-lg bg-gray-50">
                  <div className="font-bold text-xs text-gray-900">3. Region-Specific Dosages</div>
                  <div className="text-[11px] text-gray-500 mt-1">
                    Calibrate rainfed vs. irrigated recommendations for Telangana and Maharashtra.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
