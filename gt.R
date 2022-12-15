library(gt)
library(readr)
library(dplyr)

args <- commandArgs(trailingOnly=TRUE)

df <- read_csv(args[[1]])

df %>% 
    gt() %>% 
    as_raw_html() %>% 
    print()