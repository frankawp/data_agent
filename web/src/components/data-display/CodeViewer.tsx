"use client";

import { Tag } from "antd";

interface CodeViewerProps {
  code: string;
  language?: "sql" | "python" | "json";
  maxHeight?: number;
}

export function CodeViewer({ code, language = "sql", maxHeight }: CodeViewerProps) {
  // 简单的语法高亮（可以后续替换为 Monaco Editor）
  const highlightedCode = highlightSyntax(code, language);

  const langColors: Record<string, string> = {
    sql: "blue",
    python: "green",
    json: "orange",
  };

  return (
    <div
      style={{
        position: "relative",
        borderRadius: 4,
        border: "1px solid #e8e8e8",
        background: "#fafafa",
        overflow: "hidden",
      }}
    >
      <div style={{ position: "absolute", right: 8, top: 8 }}>
        <Tag color={langColors[language] || "default"} style={{ textTransform: "uppercase" }}>
          {language}
        </Tag>
      </div>
      <pre
        style={{
          padding: 16,
          paddingTop: 40,
          fontSize: 13,
          overflow: "auto",
          maxHeight: maxHeight || "none",
          margin: 0,
          background: "#fafafa",
        }}
      >
        <code dangerouslySetInnerHTML={{ __html: highlightedCode }} />
      </pre>
    </div>
  );
}

function highlightSyntax(code: string, language: string): string {
  // 使用 token 化方法避免嵌套替换问题
  if (language === "sql") {
    return highlightSQL(code);
  }

  if (language === "python") {
    return highlightPython(code);
  }

  return escapeHtml(code);
}

function highlightSQL(code: string): string {
  const keywords = new Set([
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "ON", "AND", "OR", "NOT", "IN", "LIKE", "ORDER", "BY", "GROUP",
    "HAVING", "LIMIT", "OFFSET", "AS", "DISTINCT", "COUNT", "SUM",
    "AVG", "MAX", "MIN", "NULL", "IS", "BETWEEN", "UNION", "ALL",
    "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TABLE",
  ]);

  const tokens: string[] = [];
  let i = 0;

  while (i < code.length) {
    // 字符串 (单引号)
    if (code[i] === "'") {
      let str = "'";
      i++;
      while (i < code.length && code[i] !== "'") {
        str += code[i];
        i++;
      }
      if (i < code.length) str += code[i++];
      tokens.push(`<span class="text-green-600">${escapeHtml(str)}</span>`);
    }
    // 标识符或关键字
    else if (/[a-zA-Z_]/.test(code[i])) {
      let word = "";
      while (i < code.length && /[a-zA-Z0-9_]/.test(code[i])) {
        word += code[i];
        i++;
      }
      if (keywords.has(word.toUpperCase())) {
        tokens.push(`<span class="text-blue-600 font-medium">${escapeHtml(word)}</span>`);
      } else {
        tokens.push(escapeHtml(word));
      }
    }
    // 其他字符
    else {
      tokens.push(escapeHtml(code[i]));
      i++;
    }
  }

  return tokens.join("");
}

function highlightPython(code: string): string {
  const keywords = new Set([
    "import", "from", "def", "class", "if", "else", "elif", "for", "while",
    "try", "except", "finally", "return", "yield", "with", "as", "in",
    "not", "and", "or", "True", "False", "None", "print", "lambda",
    "pass", "break", "continue", "raise", "global", "nonlocal", "assert",
  ]);

  const builtins = new Set([
    "len", "range", "str", "int", "float", "list", "dict", "set", "tuple",
    "open", "type", "isinstance", "hasattr", "getattr", "setattr",
  ]);

  const tokens: string[] = [];
  let i = 0;

  while (i < code.length) {
    // 注释
    if (code[i] === "#") {
      let comment = "";
      while (i < code.length && code[i] !== "\n") {
        comment += code[i];
        i++;
      }
      tokens.push(`<span class="text-gray-500">${escapeHtml(comment)}</span>`);
    }
    // 三引号字符串
    else if (code.slice(i, i + 3) === '"""' || code.slice(i, i + 3) === "'''") {
      const quote = code.slice(i, i + 3);
      let str = quote;
      i += 3;
      while (i < code.length && code.slice(i, i + 3) !== quote) {
        str += code[i];
        i++;
      }
      if (i < code.length) {
        str += quote;
        i += 3;
      }
      tokens.push(`<span class="text-green-600">${escapeHtml(str)}</span>`);
    }
    // 单引号或双引号字符串
    else if (code[i] === '"' || code[i] === "'") {
      const quote = code[i];
      let str = quote;
      i++;
      while (i < code.length && code[i] !== quote && code[i] !== "\n") {
        if (code[i] === "\\") {
          str += code[i++];
          if (i < code.length) str += code[i++];
        } else {
          str += code[i++];
        }
      }
      if (i < code.length && code[i] === quote) str += code[i++];
      tokens.push(`<span class="text-green-600">${escapeHtml(str)}</span>`);
    }
    // 标识符或关键字
    else if (/[a-zA-Z_]/.test(code[i])) {
      let word = "";
      while (i < code.length && /[a-zA-Z0-9_]/.test(code[i])) {
        word += code[i];
        i++;
      }
      if (keywords.has(word)) {
        tokens.push(`<span class="text-purple-600 font-medium">${escapeHtml(word)}</span>`);
      } else if (builtins.has(word)) {
        tokens.push(`<span class="text-yellow-600">${escapeHtml(word)}</span>`);
      } else {
        tokens.push(escapeHtml(word));
      }
    }
    // 数字
    else if (/[0-9]/.test(code[i])) {
      let num = "";
      while (i < code.length && /[0-9.]/.test(code[i])) {
        num += code[i];
        i++;
      }
      tokens.push(`<span class="text-orange-500">${escapeHtml(num)}</span>`);
    }
    // 其他字符
    else {
      tokens.push(escapeHtml(code[i]));
      i++;
    }
  }

  return tokens.join("");
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
