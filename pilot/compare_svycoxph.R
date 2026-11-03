#!/usr/bin/env Rscript
# survey::svycoxph reference for cause-specific mortality (issue #6).
suppressPackageStartupMessages({
  library(survey)
  library(haven)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) normalizePath(args[[1]]) else normalizePath(".")
out_path <- file.path(root, "results/cause-specific-mortality/svycoxph_reference.json")
data_dir <- file.path(root, "data")

cycles <- list(
  list(sfx = "", lmf = "1999_2000"),
  list(sfx = "_B", lmf = "2001_2002"),
  list(sfx = "_C", lmf = "2003_2004")
)

label_khz <- c(
  5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 23, 25, 28, 31, 35, 39, 43, 50,
  54, 60, 67, 75, 83, 93, 100, 115, 128, 143, 159, 177, 200, 220, 245, 273, 304, 339,
  378, 421, 469, 500, 582, 649, 723, 806, 898, 1000
)
idx50 <- which(label_khz == 50)
r50 <- if (label_khz[idx50] < 1000) paste0("BIXS", sprintf("%03d", label_khz[idx50]), "K") else "BIXS1M"
x50 <- sub("BIXS", "BIXC", r50)

read_mort <- function(lmf) {
  path <- file.path(data_dir, paste0("NHANES_", lmf, "_MORT_2019_PUBLIC.dat"))
  mort <- read.fwf(
    path,
    widths = c(6, 8, 1, 1, 3, 26, 3),
    col.names = c("SEQN", "skip", "eligstat", "mortstat", "ucod_leading", "skip2", "months"),
    colClasses = c("integer", "NULL", "integer", "integer", "character", "NULL", "numeric"),
    na.strings = "."
  )
  mort$ucod_num <- suppressWarnings(as.integer(mort$ucod_leading))
  mort[, c("SEQN", "eligstat", "mortstat", "ucod_num", "months")]
}

frames <- list()
for (cy in cycles) {
  bix <- read_xpt(file.path(data_dir, paste0("BIX", cy$sfx, ".xpt")))
  bix <- bix[bix$BIAEXSTS == 1, ]
  demo <- read_xpt(file.path(data_dir, paste0("DEMO", cy$sfx, ".xpt")))
  w <- if ("WTMEC4YR" %in% names(demo)) demo$WTMEC4YR * 2 / 3 else demo$WTMEC2YR / 3
  mort <- read_mort(cy$lmf)
  bix$SEQN <- as.integer(bix$SEQN)
  demo$SEQN <- as.integer(demo$SEQN)
  x <- data.frame(
    SEQN = as.integer(bix$SEQN),
    pha50 = atan2(abs(bix[[x50]]), bix[[r50]]) * 180 / pi
  )
  x <- merge(x, demo[, c("SEQN", "RIAGENDR", "RIDAGEYR", "RIDAGEEX", "SDMVSTRA", "SDMVPSU")], by = "SEQN")
  x$male <- as.numeric(x$RIAGENDR == 1)
  x$age <- ifelse(!is.na(x$RIDAGEEX), x$RIDAGEEX / 12, x$RIDAGEYR)
  x$w <- w[match(x$SEQN, demo$SEQN)]
  x$strata <- demo$SDMVSTRA[match(x$SEQN, demo$SEQN)]
  x$psu <- demo$SDMVPSU[match(x$SEQN, demo$SEQN)]
  x <- merge(x, mort, by = "SEQN", all.x = TRUE)
  frames[[length(frames) + 1]] <- x
}
d <- do.call(rbind, frames)
fits <- read.csv(file.path(data_dir, "fits.csv"))
d <- merge(d, fits[, c("SEQN", "rms")], by = "SEQN")
d <- d[!is.na(d$age) & d$age >= 20 & d$eligstat == 1 & !is.na(d$mortstat) & !is.na(d$months) & d$rms < 0.02 & d$w > 0, ]

event_for <- function(mort, ucod, cause) {
  if (cause == "heart") return(as.integer(mort == 1 & ucod == 1))
  if (cause == "cancer") return(as.integer(mort == 1 & ucod == 2))
  as.integer(mort == 1 & ucod >= 3 & ucod <= 10)
}

d$wt <- d$w / mean(d$w)
d$age_z <- as.numeric(scale(d$age))
d$male_z <- as.numeric(scale(d$male))
d$pha50_z <- as.numeric(scale(d$pha50))

res <- list(
  r_survey = as.character(packageVersion("survey")),
  n = nrow(d),
  all_cause_deaths = sum(d$mortstat == 1)
)
for (cause in c("heart", "cancer", "other")) {
  dd <- d
  dd$event <- event_for(dd$mortstat, dd$ucod_num, cause)
  des <- svydesign(ids = ~psu, strata = ~strata, weights = ~wt, nest = TRUE, data = dd)
  fit <- svycoxph(Surv(months, event) ~ age_z + male_z + pha50_z, design = des)
  cf <- coef(fit)
  se <- sqrt(diag(vcov(fit)))
  res[[cause]] <- list(
    deaths = sum(dd$event),
    hr_pha50_per_sd = unname(exp(cf["pha50_z"])),
    ci95_lo = unname(exp(cf["pha50_z"] - 1.96 * se["pha50_z"])),
    ci95_hi = unname(exp(cf["pha50_z"] + 1.96 * se["pha50_z"]))
  )
}

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
write_json(res, out_path, auto_unbox = TRUE, digits = 10, pretty = TRUE)
cat("Wrote", out_path, "\n")
