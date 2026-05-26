# Load necessary library
library(readxl)
library(dplyr)
library(psych)
library(tidyr)  
library(ggplot2)
library(lme4)
options(scipen=999)
# Specify the path to your Excel file
file_path <- "Enter your file path here"

# Read the Excel file into R
data <- read_excel(file_path)


# View the first few rows of the data frame
head(data)
# Convert Age, Task columns, and AILT_Score to numeric
data <- data %>%
  mutate_at(vars(Age, starts_with("Task"), AILT_Score), as.numeric)
head(data)



summary(data$Age)
sd(data$Age)

gender_counts <- table(data$Gender)
gender_proportions <- prop.table(gender_counts)
(gender_percentages <- gender_proportions * 100)

summary(data$AILT_Score)
sd(data$AILT_Score)

# Calculate Cronbach's alpha for the 10 tasks
# Select columns that start with "tasks_"
tasks_columns <- grep("^Task_", names(data), value = TRUE)
cronbach_alpha_result <- psych::alpha(data[, tasks_columns])
# Print the result
cronbach_alpha_result$total$raw_alpha #0.8851819


# regression of AI Receptivity on AI Literacy

# Mean center AI literacy measure
data$MC_Score<-data$AILT_Score-mean(data$AILT_Score)

# Calculate taskOverall as the average of all tasks per subject
data <- data %>%
  rowwise() %>%
  mutate(taskOverall = mean(c_across(starts_with("Task_")), na.rm = TRUE)) %>%
  ungroup()
data$Concept_Dummy<-0 # 0 is for shared; 1 is human
data$Concept_Dummy[data$Concept=="Concept 1"]<-1
model1 <- lm(taskOverall ~ MC_Score*Concept_Dummy, data=data)

# Get the summary of the model
summary(model1)
confint(model1)




# Ensure Concept_Dummy is treated as a factor and has both levels properly labeled
data$Concept_Dummy <- factor(ifelse(data$Concept_Dummy == 1, "Human Attributes", "Shared Attributes"))



# less prominent points
ggplot(data, aes(x = MC_Score, y = taskOverall, color = Concept_Dummy)) +
  geom_jitter(alpha = 0.15, size = 1.5, width = 0.2, height = 0.2) +  # Add jitter with reduced alpha and custom width/height
  geom_smooth(method = "lm", se = TRUE, linetype = "solid", linewidth = 1.5) +  # Add confidence bands
  labs(
    x = "AI Literacy (mean-centered)",  # Update x-axis label
    y = "AI Receptivity (relative preference for AI vs. human task completion)") +  # Update y-axis label
  theme_minimal(base_size = 15) +  # Increase base font size for readability
  scale_color_manual(values = c("Human Attributes" = "#0073C2FF", "Shared Attributes" = "#EFC000FF"),
                     labels = c("Human Attributes" = "Distinctly Human attributes", 
                                "Shared Attributes" = "Shared Attributes")) +  # Custom colors and updated legend labels
  theme(
    plot.title = element_blank(),  # Remove the figure title
    legend.position = "top",  # Move legend to the top
    legend.title = element_blank(),  # Remove legend title
    legend.text = element_text(size = 16, family = "Arial", face = "bold"),  # Legend text with Arial Bold
    axis.text = element_text(size = 14, family = "Arial", face = "bold"),  # Increase axis text size and use Arial Bold
    axis.title = element_text(size = 18, family = "Arial", face = "bold")  # Increase and bold axis titles using Arial Bold
  )




# conditional effects
# Load the packages
library(interactions)
library(jtools)
library(car)


model1 <- lm(taskOverall ~ MC_Score * Concept_Dummy, data = data)
# Probe the interaction and get simple slopes with CI and df
simple_slopes <- sim_slopes(model1, 
                            pred = "MC_Score", 
                            modx = "Concept_Dummy", 
                            confint = TRUE,  # Include confidence intervals
                            df = TRUE)       # Include degrees of freedom

# Display the results
print(simple_slopes)

# Get degrees of freedom from the model
df <- df.residual(model1)
# Run sim_slopes
simple_slopes <- sim_slopes(model1, 
                            pred = "MC_Score", 
                            modx = "Concept_Dummy", 
                            confint = TRUE)

# Display the results
print(simple_slopes)

# Print degrees of freedom
cat("Degrees of Freedom:", df, "\n")

