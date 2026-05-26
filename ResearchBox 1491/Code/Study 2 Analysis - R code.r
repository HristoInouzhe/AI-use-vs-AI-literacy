library(readxl)
library(ggplot2)
library(dplyr)

# Define the path to your file
file_path <- "Enter your file path here"

# Read the file
data <- read_excel(file_path)

# Print the first few rows of the dataset
head(data)

# checking the scoring
data <- data %>%
  mutate(sum_A1_A25 = rowSums(select(., A1:A25), na.rm = TRUE))

# Compare the calculated sum to the SC0 value for each row
data <- data %>%
  mutate(check_equal = sum_A1_A25 == SC0)

# If you just want to see if all sums match the SC0 values
(all(data$check_equal)) #[1] TRUE


# Create a new variable that is the average of the 4 assignments
data <- data %>%
  mutate(Avg_Assignment = rowMeans(select(., starts_with("Assignment")), na.rm = TRUE))

#statistics
mean(data$Age)
sd(data$Age)

summary(data$SC0)
sd(data$SC0)


gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

IMC_counts <- table(data$IMC)
IMC_proportions <- prop.table(IMC_counts)
(IMC_percentages <- IMC_proportions * 100)



# AI Literacy and IMC
cor_test_IMC <- cor.test(data$IMC, data$SC0, method = "pearson")
print(cor_test_IMC)


library(psych)

# Calculate Cronbach's alpha for the four assignments
cronbach_alpha_result <- psych::alpha(data[, c(29:32)])

# Print the result
cronbach_alpha_result$total$raw_alpha #.784


# Fit the model
model <- lm(Avg_Assignment ~ SC0, data = data)

# Print summary
summary(model)

confint(model)

# trying the model with age and gender for control
model_controls <- lm(Avg_Assignment ~ SC0+Age+Gender, data = data)

# Print summary
summary(model_controls)

confint(model_controls)

#####################################
# running the mixed effect model
library(tidyverse)
library(lme4)
library(lmerTest)

# Reshape data
long_data <- data %>%
  pivot_longer(cols = starts_with("Assignment"), 
               names_to = "Assignment", 
               values_to = "Score")

# Recode assignment variable to factor
long_data$Assignment <- factor(long_data$Assignment)

# Run mixed-effects model
model <- lmer(Score ~ SC0 + Assignment + (1 | ID), data = long_data, REML = TRUE)

# Print summary
summary(model)
confint(model)

# trying the model with age and gender for control
model_controls <- lmer(Score ~ SC0 + Assignment+Age+Gender + (1 | ID), data = long_data, REML = TRUE)

# Print summary
summary(model_controls)

confint(model_controls)

#########################
# Plotting the data
###########################+


p <- ggplot(data, aes(x = SC0)) + 
  geom_jitter(aes(y = Assignment_1, color = "Assignment_1", shape = "Assignment_1"), width = 0.2, height = 0.05, alpha = 0.5) +
  geom_jitter(aes(y = Assignment_2, color = "Assignment_2", shape = "Assignment_2"), width = 0.2, height = 0.05, alpha = 0.5) +
  geom_jitter(aes(y = Assignment_3, color = "Assignment_3", shape = "Assignment_3"), width = 0.2, height = 0.05, alpha = 0.5) +
  geom_jitter(aes(y = Assignment_4, color = "Assignment_4", shape = "Assignment_4"), width = 0.2, height = 0.05, alpha = 0.5) +
  geom_smooth(aes(y = Assignment_1, color = "Assignment_1"), method = "lm", se = TRUE, alpha = 0.2) +
  geom_smooth(aes(y = Assignment_2, color = "Assignment_2"), method = "lm", se = TRUE, alpha = 0.2) +
  geom_smooth(aes(y = Assignment_3, color = "Assignment_3"), method = "lm", se = TRUE, alpha = 0.2) +
  geom_smooth(aes(y = Assignment_4, color = "Assignment_4"), method = "lm", se = TRUE, alpha = 0.2) +
  labs(x = "AI Literacy", y = "AI Receptivity (Propensity to use AI)", color = "Assignment", shape = "Assignment") +
  scale_color_manual(values = c("Assignment_1" = "#FF5722", "Assignment_2" = "#03A9F4", 
                                "Assignment_3" = "#8BC34A", "Assignment_4" = "#9C27B0")) +
  scale_shape_manual(values = c("Assignment_1" = 21, "Assignment_2" = 22, "Assignment_3" = 23, "Assignment_4" = 24)) +
  theme_classic() +
  theme(axis.title.x = element_text(size = 18, family = "Arial", face = "bold"),
        axis.title.y = element_text(size = 18, family = "Arial", face = "bold"),
        axis.text = element_text(size = 14, family = "Arial", face = "bold"),
        legend.text = element_text(size = 14, family = "Arial", face = "bold"),
        legend.title = element_text(size = 16, family = "Arial", face = "bold"))

p
