"use client";

interface CodeViewerProps {
  code: string;
  language?: "sql" | "python" | "json";
}

export function CodeViewer({ code, language = "sql" }: CodeViewerProps) {
  // 简单的语法高亮（可以后续替换为 Monaco Editor）
  const highlightedCode = highlightSyntax(code, language);

  return (
    <div className="relative rounded-lg border bg-gray-50 overflow-hidden">
      <div className="absolute right-2 top-2">
        <span className="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-600 uppercase">
          {language}
        </span>
      </div>
      <pre className="p-4 text-sm overflow-auto">
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
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
