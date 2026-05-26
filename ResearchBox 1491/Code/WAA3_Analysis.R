
######################################################
# Factor loading analysis
######################################################


library(readxl)
library(psych)

# Define the path to your Excel file
excel_file <- "Enter your file path here"

# Get the names of all sheets in the Excel file
sheet_names <- excel_sheets(excel_file)

# Loop through each sheet name and assign it to a data frame in the global environment
for(sheet_name in sheet_names) {
  assign(sheet_name, read_excel(excel_file, sheet = sheet_name))
}

# "S2_25_item"    "S3_17_item"    "S4_25_item"    "S5_17_item" "S6_25_item" "S7_17_item" "SW2_17_item"

combined_25<-rbind(S2_25_item,S4_25_item,S6_25_item)
combined_17<-rbind(S3_17_item,S5_17_item,S7_17_item,SW2_17_item)

data_frame_names <- c("combined_25","combined_17")

# Filter, remove the 'filter_$' column, and handle missing or infinite values for each data frame
for(name in data_frame_names) {
  df <- get(name)
  
  # Filter rows where filter_$ is 1 and remove the 'filter_$' column
  df <- df[df$'filter_$' == 1, -which(names(df) == 'filter_$')]
  
  # Remove rows with NA, NaN, or Inf values
  df <- na.omit(df)
  df <- df[apply(df, 1, function(row) all(is.finite(row))), ]
  
  # Assign the modified data frame back to its original name
  assign(name, df)
}


# Run Exploratory Factor Analysis with a number of factors up to the number of items
fa_combined_25 <- principal(combined_25, nfactors = ncol(combined_25), rotate = "varimax")

# Extract eigenvalues from the factor analysis result
eigenvalues_25 <- fa_combined_25$values

# Create a scree plot manually
plot(eigenvalues_25, type = 'b', xlab = "Factor number", ylab = "Eigenvalue",
     main = "Scree Plot", ylim = c(0, max(eigenvalues_25, na.rm = TRUE)))



# Run Exploratory Factor Analysis with a number of factors up to the number of items
fa_combined_17 <- principal(combined_17, nfactors = ncol(combined_17), rotate = "varimax")

# Extract eigenvalues from the factor analysis result
eigenvalues_17 <- fa_combined_17$values

# Create a scree plot manually
plot(eigenvalues_17, type = 'b', xlab = "Factor number", ylab = "Eigenvalue",
     main = "Scree Plot", ylim = c(0, max(eigenvalues_17, na.rm = TRUE)))





######################################################
# Factor loading analysis
######################################################



library(readxl)
library(psych)
library(dplyr)

# Define the path to your Excel file
excel_file <- "Enter your file path here"

# Get the names of all sheets in the Excel file
sheet_names <- excel_sheets(excel_file)

# Loop through each sheet name and assign it to a data frame in the global environment
for(sheet_name in sheet_names) {
  assign(sheet_name, read_excel(excel_file, sheet = sheet_name))
}

# "S2_25_item"    "S3_17_item"    "S4_25_item"    "S5_17_item" "S6_25_item" "S7_17_item" "SW2_17_item"


data_frame_names <- c("S2_25_item","S3_17_item","S4_25_item","S5_17_item","S6_25_item","S7_17_item","SW2_17_item")

# Filter, remove the 'filter_$' column, and handle missing or infinite values for each data frame
for(name in data_frame_names) {
  df <- get(name)
  
  # Filter rows where filter_$ is 1 and remove the 'filter_$' column
  df <- df[df$'filter_$' == 1, -which(names(df) == 'filter_$')]
  
  # Assign the modified data frame back to its original name
  assign(name, df)
}


S2_25_item$Study<-"Study2"
S3_17_item$Study<-"Study3"
S4_25_item$Study<-"Study4"
S5_17_item$Study<-"Study5"
S6_25_item$Study<-"Study6"
S7_17_item$Study<-"Study7"
SW2_17_item$Study<-"StudySW2"

# calculate score
S2_25_item <- S2_25_item %>%
  mutate(AILT_25 = rowSums(select(., A1:A25), na.rm = TRUE))
S3_17_item <- S3_17_item %>%
  mutate(AILT_17 = rowSums(select(., A1:A17), na.rm = TRUE))
S4_25_item <- S4_25_item %>%
  mutate(AILT_25 = rowSums(select(., A1:A25), na.rm = TRUE))
S5_17_item <- S5_17_item %>%
  mutate(AILT_17 = rowSums(select(., A1:A17), na.rm = TRUE))
S6_25_item <- S6_25_item %>%
  mutate(AILT_25 = rowSums(select(., A1:A25), na.rm = TRUE))
S7_17_item <- S7_17_item %>%
  mutate(AILT_17 = rowSums(select(., A1:A17), na.rm = TRUE))
SW2_17_item <- SW2_17_item %>%
  mutate(AILT_17 = rowSums(select(., A1:A17), na.rm = TRUE))

#standardize dv
S2_25_item$DV_standardized <- scale(S2_25_item$DV, center = TRUE, scale = TRUE)
S3_17_item$DV_standardized <- scale(S3_17_item$DV, center = TRUE, scale = TRUE)
S4_25_item$DV_standardized <- scale(S4_25_item$DV, center = TRUE, scale = TRUE)
S5_17_item$DV_standardized <- scale(S5_17_item$DV, center = TRUE, scale = TRUE)
S6_25_item$DV_standardized <- scale(S6_25_item$DV, center = TRUE, scale = TRUE)
S7_17_item$DV_standardized <- scale(S7_17_item$DV, center = TRUE, scale = TRUE)
SW2_17_item$DV_standardized <- scale(SW2_17_item$DV, center = TRUE, scale = TRUE)

combined_25<-rbind(S2_25_item,S4_25_item,S6_25_item)
combined_17<-rbind(S3_17_item,S5_17_item,SW2_17_item)

combined_25 <- combined_25 %>%
  mutate(
    sum_Fac1 = rowSums(select(., c(A5, A6, A7, A10, A11, A14, A24)), na.rm = TRUE),
    sum_Fac2 = rowSums(select(., c(A1, A2, A3, A4, A8, A9, A12, A13, A15, A16, A17, A18, A19, A20, A21, A22, A23, A25)), na.rm = TRUE)
  )

combined_17 <- combined_17 %>%
  mutate(
    sum_Fac1 = rowSums(select(., c( A2, A4, A5, A6, A10, A13, A16)), na.rm = TRUE),
    sum_Fac2 = rowSums(select(., c(A1, A3, A7, A8,A9, A11, A12, A14, A15, A17)), na.rm = TRUE)
  )

# Perform linear regression with AILT_25 as the IV and DV_standardized as the DV
model_25 <- lm(DV_standardized ~ AILT_25+Study, data = combined_25)
model_25F1 <- lm(DV_standardized ~ sum_Fac1+Study, data = combined_25)
model_25F2 <- lm(DV_standardized ~ sum_Fac2+Study, data = combined_25)


# Display the summary of the regression model
summary(model_25)
confint(model_25)
summary(model_25F1)
confint(model_25F1)
summary(model_25F2)
confint(model_25F2)

# Perform linear regression with AILT_17 as the IV and DV_standardized as the DV
model_17 <- lm(DV_standardized ~ AILT_17+Study, data = combined_17)
model_17F1 <- lm(DV_standardized ~ sum_Fac1+Study, data = combined_17)
model_17F2 <- lm(DV_standardized ~ sum_Fac2+Study, data = combined_17)

# Display the summary of the regression model
summary(model_17)
confint(model_17)
summary(model_17F1)
confint(model_17F1)
summary(model_17F2)
confint(model_17F2)

