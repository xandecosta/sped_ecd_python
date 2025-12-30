# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Configuracoes Gerais ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## define diretorio do script ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
require(rstudioapi)
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
options(java.parameters = "-Xmx4000m")
rm(list = ls())                                   

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## carrega bilbiotecas ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

library(tidyverse)
library(magrittr)
library(stringr)
library(readr)
library(lubridate)
library(readxl)
library(writexl)
library(data.table)
library(janitor)
library(fs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## define diretorio de teste e caminhos dos arquivos ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PathInput  <- paste('./_Input/ECD/PomiFrutas/', sep = "")
PathOutput <- paste('./_Output/PomiFrutas/',    sep = "")

ListaECD <- list.files(PathInput, pattern = "\\.txt$")

# NomeListaECD <- tools::file_path_sans_ext(ListaECD)
# NListaECD <- seq_along(ListaECD)
# NListaECD1 <- NListaECD

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Funcoes   ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Converter colunas que começam com "VL" em números ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

converter_valores <- function(df) {
  df %>%
    mutate(across(starts_with("VL"),
                  ~ as.numeric(gsub(",", ".", .x))))
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Converter colunas que começam com "DT" em datas ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

converter_data <- function(df) {
  df %>%
    mutate(across(starts_with("DT"),
                  ~ dmy(.x)))
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Remover sufixos de colunas ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

remover_sufixo_coluna <- function(df) {
  df %>%
    rename_with(~ gsub("\\.[^.]+$", "", .x))  
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Extrair assinatura da ECD e salvar J800 ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

extrair_e_salvar_J800 <- function(dfECD, PeriodoECD, PathOutput) {
  
  # Limita ao registro |9999|
  
  pos_9999 <- which(str_detect(dfECD[,1], "^\\|9999\\|"))[1]
  
  if (is.na(pos_9999)) {
    
    stop("Registro |9999| não encontrado no arquivo.")
    
  }
  
  dfECD_filtrado <- dfECD[1:pos_9999, , drop = FALSE]
  
  # Identificação dos blocos J800
  
  pos_J800_all    <- which(str_detect(dfECD_filtrado[,1], "^\\|J800\\|"))
  pos_J800FIM_all <- which(str_detect(dfECD_filtrado[,1], "\\|J800FIM\\|$"))
  
  if (length(pos_J800_all) > 0 && length(pos_J800FIM_all) > 0) {
    
    pasta_j800 <- file.path(PathOutput, paste0("J800_", PeriodoECD)) # Cria pasta de saída se necessário
    
    if (!dir_exists(pasta_j800)) {
      
      dir_create(pasta_j800)
      message("Pasta criada: ", pasta_j800)
      
    }
    
    for (idx in seq_along(pos_J800_all)) {
      
      inicio <- pos_J800_all[idx]
      fim    <- pos_J800FIM_all[idx]
      
      if (inicio > fim) {
        
        warning(paste("Bloco J800", idx, "ignorado: |J800| ocorre após |J800FIM|."))
        next
        
      }
      
      bloco_j800 <- dfECD_filtrado[inicio:fim, 1]
      
      # Mantem o texto do rtf excluindo tags incluidas pelo PVA ECD
      bloco_j800[1] <- str_replace(bloco_j800[1], ".*(?=\\{\\\\rtf1\\\\)", "")
      bloco_j800    <- str_replace(bloco_j800, "\\|J800FIM\\|$", "")
      
      texto_j800 <- paste(bloco_j800, collapse = "\n")
      
      # Nome do arquivo .rtf
      nome_arquivo_rtf <- paste0("J800_", PeriodoECD, "_", str_pad(idx, 2, pad = "0"), ".rtf")
      caminho_arquivo_rtf <- file.path(pasta_j800, nome_arquivo_rtf)
      
      # Salva diretamente como .rtf
      write_file(texto_j800, file = caminho_arquivo_rtf)
      
      message("Arquivo salvo: ", caminho_arquivo_rtf)
    }
    
    # Remove blocos J800 do dataframe para seguir o pipeline
    linhas_remover <- unlist(mapply(seq, pos_J800_all, pos_J800FIM_all))
    dfECD_filtrado <- dfECD_filtrado[-linhas_remover, , drop = FALSE]
    
  } else {
    
    message("Nenhum registro J800 encontrado em ", PeriodoECD)
    
  }
  
  return(dfECD_filtrado)
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Agrupar objetos por padrão e exportar para xlsx e rds ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

exportar_objetos <- function(pattern_objetos, nome_arquivo, path_saida = PathOutput) {
  
  # Lista nomes dos objetos no ambiente global pelo padrão
  nomes_objetos <- ls(pattern = pattern_objetos, envir = .GlobalEnv)
  
  if (length(nomes_objetos) > 0) {
    
    lista_objetos <- lapply(nomes_objetos, get, envir = .GlobalEnv)
    names(lista_objetos) <- nomes_objetos
    
    # salva objetos no formato xlsx
    caminho_xlsx <- file.path(path_saida, nome_arquivo)
    write_xlsx(lista_objetos, path = caminho_xlsx)
    message("Arquivo gerado (.xlsx): ", caminho_xlsx)
    
    # cria pasta R_Output/arquivos_RDS
    pasta_rds <- file.path(path_saida, "arquivos_RDS")
    if (!dir_exists(pasta_rds)) {
      dir_create(pasta_rds)
      message("Pasta criada: ", pasta_rds)
    }
    
    # salva arquivo .rds
    nome_rds <- str_replace(nome_arquivo, "\\.xlsx$", ".rds")
    caminho_rds <- file.path(pasta_rds, nome_rds)
    saveRDS(lista_objetos, caminho_rds)
    message("Arquivo gerado (.rds): ", caminho_rds)
    
    # salva arquivo _objetos.txt
    caminho_objetos_txt <- str_replace(caminho_rds, "\\.rds$", "_objetos.txt")
    writeLines(nomes_objetos, caminho_objetos_txt)
    message("Lista de objetos salva: ", caminho_objetos_txt)
    
    # atualizar log fixo RDS_Gerados.txt
    caminho_log_rds <- file.path(pasta_rds, "RDS_Gerados.txt")
    
    if (file.exists(caminho_log_rds)) {
      linhas_existentes <- readLines(caminho_log_rds)
    } else {
      linhas_existentes <- character(0)
    }
    
    linhas_atualizadas <- unique(c(linhas_existentes, basename(caminho_rds)))
    writeLines(linhas_atualizadas, caminho_log_rds)
    
    message("Log atualizado: ", caminho_log_rds)
    
  } else {
    
    message("Nenhum objeto encontrado para o padrão: ", pattern_objetos)
    
  }
  
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Funcao para exportar objetos em lote | xlsx e RDS ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

exportar_lote <- function(exportacoes, path_saida = PathOutput) {
  
  for (exp in exportacoes) {
    pattern <- exp$pattern
    nome <- exp$nome
    
    exportar_objetos(
      pattern_objetos = pattern,
      nome_arquivo = nome,
      path_saida = path_saida
    )
  }
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## Funcao para recuperar RDS ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

recuperar_objetos <- function() {
  
  # Define a pasta R_Output/arquivos_RDS automaticamente
  pasta_rds <- file.path("_Output", "PomiFrutas", "arquivos_RDS")
  
  if (!dir.exists(pasta_rds)) {
    stop("A pasta R_Output/arquivos_RDS não existe. Verifique o pipeline de geração dos arquivos RDS.")
  }
  
  caminho_log_rds <- file.path(pasta_rds, "RDS_Gerados.txt")
  
  if (!file.exists(caminho_log_rds)) {
    stop("Arquivo de log RDS_Gerados.txt não encontrado em: ", pasta_rds)
  }
  
  arquivos_rds <- readLines(caminho_log_rds)
  
  for (arquivo in arquivos_rds) {
    caminho_rds <- file.path(pasta_rds, arquivo)
    
    if (!file.exists(caminho_rds)) {
      warning("Arquivo RDS não encontrado: ", caminho_rds)
      next
    }
    
    lista_objetos <- readRDS(caminho_rds)
    caminho_objetos_txt <- str_replace(caminho_rds, "\\.rds$", "_objetos.txt")
    
    if (!file.exists(caminho_objetos_txt)) {
      warning("Arquivo de nomes de objetos não encontrado: ", caminho_objetos_txt)
      next
    }
    
    nomes_objetos <- readLines(caminho_objetos_txt)
    
    for (nome in nomes_objetos) {
      if (!is.null(lista_objetos[[nome]])) {
        assign(nome, lista_objetos[[nome]], envir = .GlobalEnv)
        message("Objeto restaurado: ", nome)
      } else {
        warning("Objeto ", nome, " não encontrado no arquivo RDS: ", arquivo)
      }
    }
  }
  
  message("Todos os arquivos RDS processados e objetos restaurados no ambiente global.")
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Biblioteca de Tabelas ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

tb_natureza_contas <- tibble(
  cod = c("01", "02", "03", "04", "05", "09"),
  descricao = c(
    "Ativo",
    "Passivo",
    "Patrimonio Liquido",
    "Resultado",
    "Compensacao",
    "Outras"
  )
)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Processamento dos arquivo de ECD ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

for (i in seq_along(ListaECD)) {
  
  dfECD <- as.data.frame(read.delim(paste(PathInput, ListaECD[i], sep = ""), fileEncoding = "CP1252", header = FALSE))
  
  linha_0000    <- dfECD[1, 1]
  campos_0000   <- str_split(linha_0000, "\\|")[[1]]
  data_inicial  <- dmy(campos_0000[4])  # posição após o 3º pipe
  data_final    <- dmy(campos_0000[5])  # posição após o 4º pipe
  
  PeriodoECD    <- format(data_final, "%Y%m%d")
  
  ## aplica funcao de extrair assinatura e salvar registros J800 ##
  
  dfECD <- extrair_e_salvar_J800(dfECD, PeriodoECD, PathOutput)
  
  names(dfECD)  <- "TEXTOREG" 
  dfECD$REG     <- substr(dfECD$TEXTOREG,2,5) 
  dfECD$COUNTER <- 1:length(dfECD$TEXTOREG)
  dfECD$COUNTER <- str_pad(dfECD$COUNTER, 8, pad = "0")
  dfECD$PK      <- paste(PeriodoECD, dfECD$COUNTER, sep = "_")
  dfECD         <- dfECD[,c("PK","REG","TEXTOREG")]
  
  ListaRegistrosECD <- unique(dfECD$REG) 
  
  # separa arquivo de ECD por blocos
  
  for (j in seq_along(ListaRegistrosECD))
  {
    
    dfECD %>% dplyr::filter(REG == ListaRegistrosECD[j]) -> d 
    d %<>% separate(TEXTOREG, paste("X", 1:30, sep = ""), sep = "\\|")
    #d %<>% str_split(TEXTOREG, "\\|")
    assign(paste("dfECD", ListaRegistrosECD[j], sep = "_"),d)
    rm(d)
    
  }
  gc()
  
  # trata registros
  
  if (exists("dfECD_I010")) {
    dfECD_I010 %<>% 
      select(1, 5, 6) %>% 
      setnames(c("PK", "IND_ESC", "COD_VER_LC"))
    
    versao_ECD_limpa <- sub("\\..*", "", dfECD_I010$COD_VER_LC)
    versao_ECD <- dfECD_I010$COD_VER_LC
  }
  
  if (exists("dfECD_I050")) {
    dfECD_I050 %<>% 
      select(1, 5:11) %>% 
      setnames(c("PK", "DT_ALT", "COD_NAT", "IND_CTA", 
                 "NIVEL", "COD_CTA", "COD_CTA_SUP", "CTA")) %>% 
      mutate(NIVEL = as.numeric(NIVEL)) %>% 
      converter_data() %>% 
      mutate(CTA = str_squish(toupper(CTA)))
  }
  
  if (exists("dfECD_I051")) {
    dfECD_I051 %<>% 
      select(1, 5:6) %>% 
      setnames(c("PK", "COD_CCUS", "COD_CTA_REF"))
  }
  
  if (exists("dfECD_I052")) {
    dfECD_I052 %<>% 
      select(1, 5:6) %>% 
      setnames(c("PK", "COD_CCUS", "COD_AGL"))
  }
  
  if (exists("dfECD_I150")) {
    dfECD_I150 %<>% 
      select(1, 5:6) %>% 
      setnames(c("PK", "DT_INI", "DT_FIN")) %>% 
      converter_data()
  }
  
  if (exists("dfECD_I155")) {
    dfECD_I155 %<>% 
      select(1, 5:18) %>% 
      setnames(c("PK", "COD_CTA", "COD_CCUS", 
                 "VL_SLD_INI", "IND_DC_INI", 
                 "VL_DEB", "VL_CRED", 
                 "VL_SLD_FIN", "IND_DC_FIN",
                 "VL_SLD_INI_MF", "IND_DC_INI_MF", 
                 "VL_DEB_MF", "VL_CRED_MF", 
                 "VL_SLD_FIN_MF", "IND_DC_FIN_MF")) %>% 
      converter_valores()
  }
  
  if (exists("dfECD_I200")) {
    dfECD_I200 %<>%
      select(1, 5:10) %>% 
      setnames(c("PK", "NUM_LCTO", "DT_LCTO", "VL_LCTO", 
                 "IND_LCTO", "DT_LCTO_EXT", "VL_LCTO_MF")) %>% 
      converter_data() %>% 
      converter_valores()
  }
  
  if (exists("dfECD_I250")) {
    dfECD_I250 %<>% 
      select(1, 5:14) %>% 
      setnames(c("PK", "COD_CTA", "COD_CCUS", "VL_DC", "IND_DC", 
                 "NUM_ARQ", "COD_HIST_PAD", "HIST", "COD_PART", 
                 "VL_DC_MF", "IND_DC_MF")) %>% 
      converter_valores() %>% 
      mutate(HIST = str_squish(toupper(HIST)))
  }  
  
  if (exists("dfECD_J005")) {
    dfECD_J005 %<>% 
      select(1, 5:6) %>% 
      setnames(c("PK", "DT_INI", "DT_FIN")) %>% 
      converter_data()
  }
  
  if (exists("dfECD_J100")) {
    
    if (versao_ECD_limpa %in% c("1", "2", "3", "4")) {
      
      dfECD_J100 %<>% 
        select(1, 5:10) %>% 
        setnames(c("PK", "COD_AGL", "NIVEL_AGL", 
                   "IND_GRP_BAL", "DESCR_COD_AGL", 
                   "VL_CTA_FIN", "IND_DC_CTA_FIN"))
      
    } else if (versao_ECD_limpa %in% c("5")) {
      
      dfECD_J100 %<>% 
        select(1, 5:12) %>% 
        setnames(c("PK", "COD_AGL", "NIVEL_AGL", 
                   "IND_GRP_BAL", "DESCR_COD_AGL", 
                   "VL_CTA_FIN", "IND_DC_CTA_FIN", 
                   "VL_CTA_INI", "IND_DC_CTA_INI"))
      
    } else if (versao_ECD_limpa %in% c("6", "7", "8", "9"))  {
      
      dfECD_J100 %<>% 
        select(1, 5:15) %>% 
        setnames(c("PK", "COD_AGL", "IND_COD_AGL", "NIVEL_AGL", 
                   "COD_AGL_SUP", "IND_GRP_BAL", "DESCR_COD_AGL", 
                   "VL_CTA_INI", "IND_DC_CTA_INI",
                   "VL_CTA_FIN", "IND_DC_CTA_FIN", "NOTA_EXP_REF"))
      
    }
    
    dfECD_J100 %<>%
      mutate(NIVEL_AGL = as.numeric(NIVEL_AGL), 
             DESCR_COD_AGL = str_squish(toupper(DESCR_COD_AGL))) %>% 
      converter_valores()
    
  }
  
  if (exists("dfECD_J150")) {
    
    if (versao_ECD_limpa %in% c("1", "2", "3")) {
      
      dfECD_J150 %<>% 
        select(1, 5:9) %>% 
        setnames(c("PK", "COD_AGL", "NIVEL_AGL", "DESCR_COD_AGL", 
                   "VL_CTA_FIN", "IND_DC_CTA_FIN"))
      
    } else if (versao_ECD_limpa %in% c("4")) {
      
      dfECD_J150 %<>% 
        select(1, 5:11) %>% 
        setnames(c("PK", "COD_AGL", "NIVEL_AGL", "DESCR_COD_AGL", 
                   "VL_CTA_FIN", "IND_DC_CTA_FIN", 
                   "VL_CTA_INI", "IND_DC_CTA_INI"))
      
    } else if (versao_ECD_limpa %in% c("5", "6", "7", "8", "9"))  {
      
      dfECD_J150 %<>% 
        select(1, 5:16) %>% 
        setnames(c("PK", "NU_ORDEM", "COD_AGL", "IND_COD_AGL", 
                   "NIVEL_AGL", "COD_AGL_SUP", "DESCR_COD_AGL", 
                   "VL_CTA_INI", "IND_DC_CTA_INI", 
                   "VL_CTA_FIN", "IND_DC_CTA_FIN", 
                   "IND_GRP_DRE", "NOTA_EXP_REF"))
    }
    
    dfECD_J150 %<>%
      mutate(NIVEL_AGL = as.numeric(NIVEL_AGL), 
             DESCR_COD_AGL = str_squish(toupper(DESCR_COD_AGL))) %>% 
      converter_valores()
    
  }
  
  
  # Plano de Contas
  
  df_plano_contas <- 
    dfECD_I050 %>% 
    mutate(CONTA = paste(COD_CTA, CTA, sep = " - "))
  
  assign(paste("PlanoContas_", PeriodoECD, sep = ""), df_plano_contas)
  
  
  # Saldos mensais das contas analiticas
  
  df_saldos_mensais_contas_analiticas <- 
    dfECD_I150 %>% 
    full_join(dfECD_I155, "PK") %>% 
    arrange(PK) %>% 
    fill(DT_INI, DT_FIN) %>% 
    filter(!is.na(COD_CTA))
  
  assign(paste("SaldoContas_", PeriodoECD, sep = ""), df_saldos_mensais_contas_analiticas)
  
  
  # lancamentos contabeis
  
  df_lancamentos <- 
    dfECD_I200 %>% 
    full_join(dfECD_I250, "PK") %>% 
    arrange(PK) %>% 
    fill(NUM_LCTO, DT_LCTO, IND_LCTO, DT_LCTO_EXT, VL_LCTO_MF) %>% 
    filter(!is.na(VL_DC)) %>% 
    mutate(VL_D = ifelse(IND_DC == "D", VL_DC, NA),
           VL_C = ifelse(IND_DC == "C", VL_DC, NA),
           VL_LCTO = ifelse(IND_DC == "D", VL_DC, -VL_DC)) %>% 
    left_join(df_plano_contas, "COD_CTA") %>% 
    select(1:8, 10:19, 21:27) %>% 
    remover_sufixo_coluna()
  
  assign(paste("Lctos_", PeriodoECD, sep = ""), df_lancamentos)
  
  
  # balanco patrimonial
  
  df_balanco_patrimonial <- 
    dfECD_J005 %>% 
    full_join(dfECD_J100, "PK") %>% 
    arrange(PK) %>% 
    fill(DT_INI, DT_FIN) %>% 
    filter(!is.na(COD_AGL))
  
  assign(paste("BalPatrim_", PeriodoECD, sep = ""), df_balanco_patrimonial)  
  
  
  # demonstracao de resultados
  
  df_demonstracao_resultados <- 
    dfECD_J005 %>% 
    full_join(dfECD_J150, "PK") %>% 
    arrange(PK) %>% 
    fill(DT_INI, DT_FIN) %>% 
    filter(!is.na(COD_AGL))
  
  assign(paste("DemResultado_", PeriodoECD, sep = ""), df_demonstracao_resultados)  
  
  
  # balancetes mensais 
  
  unique_DtFinSaldos <- unique(df_saldos_mensais_contas_analiticas$DT_FIN)
  Balancetes_PeriodoECD <- tibble()
  
  for (data_mes in unique_DtFinSaldos) {
    
    AMD <- as.Date(data_mes)
    
    # 1️⃣ Ajusta os saldos do mês e sinal
    tb_SaldoMes <- 
      df_saldos_mensais_contas_analiticas %>%
      filter(DT_FIN == data_mes) %>%
      mutate(
        VL_SLD_INI = ifelse(IND_DC_INI == "D", VL_SLD_INI, -VL_SLD_INI),
        VL_SLD_FIN = ifelse(IND_DC_FIN == "D", VL_SLD_FIN, -VL_SLD_FIN)
      ) %>%
      select(COD_CTA, VL_SLD_INI, VL_DEB, VL_CRED, VL_SLD_FIN)
    
    # 2️⃣ Inicializa a tabela base
    tabela_base <- 
      df_plano_contas %>%
      left_join(tb_SaldoMes, by = "COD_CTA")
    
    tabela_base[is.na(tabela_base)] <- 0
    
    # 3️⃣ Propagação dinâmica
    
    tabela_atual <- tabela_base
    repetir <- TRUE
    
    while (repetir) {
      
      agregados <- 
        tabela_atual %>%
        group_by(COD_CTA_SUP) %>%
        summarise(
          VL_SLD_INI = sum(VL_SLD_INI, na.rm = TRUE),
          VL_DEB     = sum(VL_DEB, na.rm = TRUE),
          VL_CRED    = sum(VL_CRED, na.rm = TRUE),
          VL_SLD_FIN = sum(VL_SLD_FIN, na.rm = TRUE),
          .groups = "drop"
        )
      
      tabela_nova <- 
        tabela_base %>%
        left_join(agregados, by = c("COD_CTA" = "COD_CTA_SUP"), suffix = c("", ".y")) %>%
        rowwise() %>%
        mutate(
          VL_SLD_INI = sum(VL_SLD_INI, VL_SLD_INI.y, na.rm = TRUE),
          VL_DEB     = sum(VL_DEB,     VL_DEB.y,     na.rm = TRUE),
          VL_CRED    = sum(VL_CRED,    VL_CRED.y,    na.rm = TRUE),
          VL_SLD_FIN = sum(VL_SLD_FIN, VL_SLD_FIN.y, na.rm = TRUE)
        ) %>%
        select(-ends_with(".y"))
      
      # Verifica se houve alteração
      
      repetir <- !identical(tabela_atual$VL_SLD_FIN, tabela_nova$VL_SLD_FIN)
      tabela_atual <- tabela_nova
      
    }
    
    # 4️⃣ Resultado final do mês
    df_mes_final <- 
      tabela_atual %>%
      mutate(MES = AMD) %>%
      select(COD_CTA, CTA, CONTA, NIVEL, MES, VL_SLD_INI, VL_DEB, VL_CRED, VL_SLD_FIN)
    
    Balancetes_PeriodoECD <- bind_rows(Balancetes_PeriodoECD, df_mes_final)
  
  }
  
  assign(paste0("Balancetes_", PeriodoECD), Balancetes_PeriodoECD, envir = .GlobalEnv)
  
  
  rm(list = ls()[grep("^dfECD", ls())])
  rm(list = ls()[grep("^df_", ls())])
  rm(list = ls()[grep("^bm_", ls())])
  rm(list = ls()[grep("^Balancetes_PeriodoECD", ls())])
  
  
  periodo_padrao <- paste0(PeriodoECD, "$")
  objetos_periodo <- ls(pattern = periodo_padrao)
  lista_objetos <- lapply(objetos_periodo, get)
  names(lista_objetos) <- objetos_periodo       # atribui nome aos elementos da lista
  write_xlsx(lista_objetos,paste(PathOutput, "PomiFrutas - ECD Completas ", PeriodoECD, ".xlsx",  sep = "")) # salva lista em arquivo xlsx
  rm(lista_objetos)
  
}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Agrupo Objetos e Exporta xlsx e rds ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Lista de exportações: padrão e nome do arquivo

exportacoes <- list(
  list(pattern = "^PlanoContas_",  nome = "PomiFrutas - ECD Completas - Plano de Contas.xlsx"),
  list(pattern = "^SaldoContas_",  nome = "PomiFrutas - ECD Completas - Saldos Contas Analiticas.xlsx"),
  list(pattern = "^Lctos_",        nome = "PomiFrutas - ECD Completas - Lancamentos.xlsx"),
  list(pattern = "^BalPatrim_",    nome = "PomiFrutas - ECD Completas - BP Balanco Patrimonial.xlsx"),
  list(pattern = "^DemResultado_", nome = "PomiFrutas - ECD Completas - DRE Demonstracao Resultado Exercicio.xlsx"),
  list(pattern = "^Balancetes_",   nome = "PomiFrutas - ECD Completas - Balancetes.xlsx")
)

# exporta arquivos xlsx e rds
exportar_lote(exportacoes)

# recupera objetos dos arquivos rds
# recuperar_objetos()



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Recupera Objetos rds ####
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# recupera objetos dos arquivos rds

recuperar_objetos()


# consolida lancamentos para analise

Full_Lctos <- 
  bind_rows(lapply(ls(pattern = "^Lctos"),   get)) %>% 
  mutate(LCTO_PK = paste0(NUM_LCTO, "_", DT_LCTO))


# Partes Relacionadas

## movimentacao de Partes Relacionadas

ParteRelacionadas_Mov_NumLcto <- 
  Full_Lctos %>% 
  filter(COD_CTA == "004293" |
           COD_CTA == "005351" |
           COD_CTA == "2116100002")

ParteRelacionadas_Mov_Lcto <- 
  Full_Lctos %>% 
  filter(LCTO_PK %in% ParteRelacionadas_Mov_NumLcto$LCTO_PK,
         IND_LCTO != "E")

write_xlsx(ParteRelacionadas_Mov_Lcto, paste(PathOutput, "PomiFrutas - Analise Partes Relacionadas.xlsx", sep = ""))




# Partes Relacionadas
`mutuo edgar sfadie - 005458`
## movimentacao de Partes Relacionadas

MutuoSafdie_Mov_NumLcto <- 
  Full_Lctos %>% 
  filter(COD_CTA == "005458" |
           COD_CTA == "2115020022" |
           COD_CTA == "2115020030" |
           COD_CTA == "2213010011")

MutuoSafdie_Mov_Lcto <- 
  Full_Lctos %>% 
  filter(LCTO_PK %in% MutuoSafdie_Mov_NumLcto$LCTO_PK,
         IND_LCTO != "E")

write_xlsx(MutuoSafdie_Mov_Lcto, paste(PathOutput, "PomiFrutas - Analise Mutuo Eduardo Safdie.xlsx", sep = ""))



