<?php

// =============================
// Utils
// =============================

function extrair_versao(string $nome): array {
    if (preg_match('/One\.repo-(\d+(?:\.\d+)*)\.zip/', $nome, $m)) {
        return array_map('intval', explode('.', $m[1]));
    }
    return [];
}

function pasta_tem_zip_recursivo(string $pasta): bool {
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($pasta, FilesystemIterator::SKIP_DOTS)
    );
    foreach ($iterator as $file) {
        if (strtolower($file->getExtension()) === 'zip') {
            return true;
        }
    }
    return false;
}

function remover_acentos(string $texto): string {
    $texto = iconv('UTF-8', 'ASCII//TRANSLIT', $texto);
    return strtolower($texto);
}

// =============================
// Repositórios mais recentes
// =============================

function encontrar_repos_mais_recentes(string $raiz): array {
    $encontrados = [];

    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($raiz, FilesystemIterator::SKIP_DOTS)
    );

    foreach ($iterator as $file) {
        if (preg_match('/One\.repo-.*\.zip$/', $file->getFilename())) {
            $versao = extrair_versao($file->getFilename());
            if ($versao) {
                $encontrados[] = [$versao, $file->getPathname()];
            }
        }
    }

    if (!$encontrados) {
        return [];
    }

    usort($encontrados, fn($a, $b) => $a[0] <=> $b[0]);
    $maior = end($encontrados)[0];

    return array_map(
        fn($e) => $e[1],
        array_filter($encontrados, fn($e) => $e[0] === $maior)
    );
}

// =============================
// Index handling
// =============================

function gerar_ou_remover_index(string $pasta, string $raiz): void {
    $index = $pasta . DIRECTORY_SEPARATOR . 'index.html';
    $tem_zip = pasta_tem_zip_recursivo($pasta);

    if ($pasta !== $raiz && !$tem_zip) {
        if (file_exists($index)) {
            unlink($index);
            echo "🧹 removido: $index\n";
        }
        return;
    }

    $repos_recentes = encontrar_repos_mais_recentes($raiz);

    if ($pasta === $raiz && !$repos_recentes) {
        if (file_exists($index)) {
            unlink($index);
            echo "🧹 removido: $index\n";
        }
        return;
    }

    $linhas_html = [
        "<!DOCTYPE html>",
        "<html lang='pt-BR'>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Directory listing</title>",
        "<style>
        body { font-family: Arial; background:#f9f9f9; padding:20px; }
        pre { background:#fff; padding:10px; border-radius:8px; }
        a { text-decoration:none; color:#0066cc; }
        #search { padding:6px; width:300px; margin-bottom:12px; }
        </style>",
        "</head>",
        "<body>",
        "<h1>Directory listing</h1>",
        "<hr/>"
    ];

    if ($pasta !== $raiz) {
        $linhas_html[] =
            '<a href="../index.html" style="display:inline-block;margin-bottom:12px;">← Voltar</a>';
    }

    $linhas_html[] = '<input type="text" id="search" placeholder="Pesquisar arquivos ou pastas...">';
    $linhas_html[] = "<pre id='listing'>";

    $itens = [];

    $dirs = scandir($pasta);
    natcasesort($dirs);

    foreach ($dirs as $item) {
        if ($item[0] === '.' || $item === 'index.html') continue;

        $path = $pasta . DIRECTORY_SEPARATOR . $item;

        if (is_dir($path) && pasta_tem_zip_recursivo($path)) {
            $linha = "📁 <a href=\"./$item/index.html\">$item/</a>";
        } elseif (is_file($path) && str_ends_with(strtolower($item), '.zip')) {
            $linha = "📦 <a href=\"./$item\">$item</a>";
        } else {
            continue;
        }

        $linhas_html[] = $linha;
        $itens[] = [remover_acentos($item), $linha];
    }

    $linhas_html[] = "</pre>";
    $linhas_html[] = "<script>
        const items = " . json_encode($itens) . ";
        const search = document.getElementById('search');
        const listing = document.getElementById('listing');

        function norm(s){return s.normalize('NFD').replace(/\\p{Diacritic}/gu,'').toLowerCase();}

        search.addEventListener('input', ()=>{
            const t = norm(search.value);
            listing.innerHTML = items.filter(i=>i[0].includes(t)).map(i=>i[1]).join('\\n');
        });
    </script>";
    $linhas_html[] = "</body></html>";

    file_put_contents($index, implode("\n", $linhas_html));
    echo "✔ index atualizado: $pasta\n";

    if ($pasta === $raiz && $repos_recentes) {
        $extra = "\n<!-- REPOSITORIO KODI (FORA DO HTML) -->\n<div style=\"display:none\"><table>";
        foreach ($repos_recentes as $repo) {
            $rel = str_replace($raiz . DIRECTORY_SEPARATOR, '', $repo);
            $extra .= "<tr><td><a href=\"$rel\">$rel</a></td></tr>";
        }
        $extra .= "</table></div>";
        file_put_contents($index, $extra, FILE_APPEND);
        echo "✔ bloco externo Kodi adicionado\n";
    }
}

// =============================
// Varredura bottom-up
// =============================

function varrer_bottom_up(string $pasta, string $raiz): void {
    foreach (scandir($pasta) as $item) {
        if ($item[0] === '.') continue;
        $path = $pasta . DIRECTORY_SEPARATOR . $item;
        if (is_dir($path)) {
            varrer_bottom_up($path, $raiz);
        }
    }
    gerar_ou_remover_index($pasta, $raiz);
}

// =============================
// Main
// =============================

$raiz = realpath('.');
varrer_bottom_up($raiz, $raiz);
gerar_ou_remover_index($raiz, $raiz);
