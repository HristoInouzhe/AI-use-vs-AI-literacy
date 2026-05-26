# Load the necessary libraries
library(readxl)
library(dplyr)
library(psych)
options(scipen=999)


file_path <- "Enter your file path here"

data <- read_excel(file_path)
data<-data[data$`filter_$`==1,]


#statistics
mean(data$Age)
sd(data$Age)

gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

summary(data$SC0)
sd(data$SC0)

####################
# Receptivity
####################


# Calculate Cronbach's alpha for the 4 Ipsos measures
cronbach_alpha_result <- psych::alpha(data[, c(23:26)])
# Print the result
cronbach_alpha_result$total$raw_alpha #.8295

# Fit the model
model <- lm(IPSOS ~ AIScore, data = data)

# Print summary
summary(model)

confint(model)

# model with controls
data$Gender_fac<-as.factor(data$Gender)
data$Income_fac<-as.factor(data$Income)
model_controls <- lm(IPSOS ~ AIScore+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model_controls)

confint(model_controls)

# check for sqrt AI score
data$sqrt_AIScore <- sqrt(data$AIScore)

model1_sqrt <- lm(IPSOS ~ sqrt_AIScore, data=data)

# Get the summary of the model
summary(model1_sqrt)
confint(model1_sqrt)



####################
# magicalness 
####################

# Calculate Cronbach's alpha for the 6 items
# Select columns that start with "magic" and a number
magical_columns <- grep("^magic.", names(data), value = TRUE)
cronbach_alpha_result <- psych::alpha(data[, magical_columns])
# Print the result
cronbach_alpha_result$total$raw_alpha #.9131


# Fit the model
model2 <- lm(magic ~ AIScore, data = data)

# Print summary
summary(model2)

confint(model2)

# model with controls
model2_controls <- lm(magic ~ AIScore+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model2_controls)

confint(model2_controls)


# check for sqrt AI score
model2_sqrt <- lm(magic ~ sqrt_AIScore, data=data)

# Get the summary of the model
summary(model2_sqrt)
confint(model2_sqrt)



####################
# awe 
####################

# Calculate Cronbach's alpha for the 4 items
# Select columns that start with "awe" and a number
awe_columns <- grep("^awe.", names(data), value = TRUE)
cronbach_alpha_result <- psych::alpha(data[, awe_columns])
# Print the result
cronbach_alpha_result$total$raw_alpha #.9182


# Fit the model
model3 <- lm(Awe4Items ~ AIScore, data = data)

# Print summary
summary(model3)

confint(model3)


# model with controls
model3_controls <- lm(Awe4Items ~ AIScore+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model3_controls)

confint(model3_controls)




# check for sqrt AI score
model3_sqrt <- lm(Awe4Items ~ sqrt_AIScore, data=data)

# Get the summary of the model
summary(model3_sqrt)
confint(model3_sqrt)


######################
# mediation check
#######################
library(psych)
library(GPArotation)
# Promax rotation
#######################
variables <- c("magic1", "magic2", "magic3", "magic4", "magic5", "magic6", 
               "awe1", "awe2", "awe3", "awe4")
fa_result_2factors <- fa(r = data[variables], nfactors = 2, fm = "pa", rotate = "promax")
print(fa_result_2factors)



# CFA Analysis
#######################
library(lavaan)
cfa_model <- '
  # Define the latent variables (factors)
  magic_factor =~ magic1 + magic2 + magic3 + magic4 + magic5 + magic6
  awe_factor =~ awe1 + awe2 + awe3 + awe4
  
  # Allow the factors to correlate
  magic_factor ~~ awe_factor
'

# Fit the model to the data using the MLR estimator for robust estimation
fit <- cfa(cfa_model, data = data, estimator = "MLR")

# Summarize the fit of the model
summary(fit, fit.measures = TRUE)



# serial mediation
#######################
# Define the serial mediation model including a direct path from AIScore to IPSOS
model <- '
# Direct paths
IPSOS ~ c * AIScore + e * Awe4Items
magic ~ a * AIScore
Awe4Items ~ b * magic

# Indirect paths
indirect_effect := a * b * e

# Note: The direct effect (c) of AIScore on IPSOS is already specified.
# The path from Awe4Items to IPSOS is represented by e to show the effect of Awe4Items
# on IPSOS, which is part of the indirect path through magic
'

# Fit the model
fit <- sem(model, data = data, se = "bootstrap", bootstrap = 10000)

# Summarize the results, focusing on standardized estimates and fit measures
summary(fit, standardized = TRUE, fit.measures = TRUE)

# Get the full parameter estimates with confidence intervals
ci_full <- parameterEstimates(fit, boot.ci.type = "bca.simple")

# Print the full results to manually inspect for the indirect effect's CI
print(ci_full)

####################
# capability 
####################

# Calculate Cronbach's alpha for the 7 items
cronbach_alpha_result <- psych::alpha(data[, c(41:47)])
# Print the result
cronbach_alpha_result$total$raw_alpha #.8254


# Fit the model
model4 <- lm(AICapability ~ AIScore, data = data)

# Print summary
summary(model4)

confint(model4)


# model with controls
model4_controls <- lm(AICapability ~ AIScore+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model4_controls)

confint(model4_controls)

# check for sqrt AI score
model4_sqrt <- lm(AICapability ~ sqrt_AIScore, data=data)

# Get the summary of the model
summary(model4_sqrt)
confint(model4_sqrt)

####################
# fear 
####################

# Calculate Cronbach's alpha for the 4 items
cronbach_alpha_result <- psych::alpha(data[, c(37:40)])
# Print the result
cronbach_alpha_result$total$raw_alpha #.87209


# Fit the model
model5 <- lm(FearItems ~ AIScore, data = data)

# Print summary
summary(model5)

confint(model5)

# model with controls
model5_controls <- lm(FearItems ~ AIScore+Age+Gender_fac+Income_fac, data = data)

# Print summary
summary(model5_controls)

confint(model5_controls)


# check for sqrt AI score
model5_sqrt <- lm(FearItems ~ sqrt_AIScore, data=data)

# Get the summary of the model
summary(model5_sqrt)
confint(model5_sqrt)
