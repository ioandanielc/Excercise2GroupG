package org.vadere.simulator.models.groups.sir;


import org.vadere.annotation.factories.models.ModelClass;
import org.vadere.simulator.models.Model;
import org.vadere.simulator.models.groups.AbstractGroupModel;
import org.vadere.simulator.models.groups.Group;
import org.vadere.simulator.models.groups.GroupSizeDeterminator;
import org.vadere.simulator.models.potential.fields.IPotentialFieldTarget;
import org.vadere.simulator.projects.Domain;
import org.vadere.state.attributes.Attributes;
import org.vadere.state.attributes.models.AttributesSIRG;
import org.vadere.state.attributes.scenario.AttributesAgent;
import org.vadere.state.scenario.DynamicElementContainer;
import org.vadere.state.scenario.Pedestrian;
import org.vadere.state.scenario.Topography;

import org.vadere.util.geometry.shapes.VPoint;
import org.vadere.util.logging.Logger;


import java.util.*;

import org.vadere.util.geometry.LinkedCellsGrid;
//test

/**
 * Implementation of groups for a susceptible / infected / removed (SIR) model.
 */
@ModelClass
public class SIRGroupModel extends AbstractGroupModel<SIRGroup> {

	private Random random;
	private LinkedHashMap<Integer, SIRGroup> groupsById;
	private Map<Integer, LinkedList<SIRGroup>> sourceNextGroups;
	private AttributesSIRG attributesSIRG;
	private Topography topography;
	private IPotentialFieldTarget potentialFieldTarget;
	private int totalInfected = 0;

	/**
	 * We have created a logger, which we have used in order to debug our implementation.
	 * We mostly used it to print when group changes took place and to tell
	 * which groups were involved in the change.
	 */

	private static Logger logger = Logger.getLogger(SIRGroupModel.class);

	/**
	 * The following 3 variables are used in our model of time_step & infection rate decoupling.
	 * We describe our time model more detailed in the report.
	 *
	 * !!!Please be advised!!!
	 * We explain the respective implementations better in the report.
	 * One should firstly, take a look at the dedicated sections from the report in order to get the basic idea of the implementation.
	 * This will make it easier to understand the code afterwards.
	 */

	/**
	 * {@link SIRGroupModel#previousSec} remembers the integer part of the last second.
	 */
	private int previousSec = -1;

	/**
	 * {@link SIRGroupModel#stepsInThisSec} remembers how many steps have we already taken in the current second.
	 * we use this to cehck if we have reached the last allowed step.
	 */
	private int stepsInThisSec = 0;

	/**
	 * {@link SIRGroupModel#maxStepsPerSec} stores how many steps per second are allowed.
	 */
	private int maxStepsPerSec = 3;

	/**
	 * {@link SIRGroupModel#ourTimeModel} set this variable to true if you want to use our timeStep-infectionRate decoupling suggestion.
	 */
	boolean ourTimeModel = true;

	/**
	 * {@link SIRGroupModel#includeRecovered} set this variable to true if you want to include the recovered/removed state/group in the simulation.
	 */
	boolean includeRecovered = true;

	/**
	 * {@link SIRGroupModel#fasterSearch} set this variable to true if you want to use the neighbour search based on {@link LinkedCellsGrid}.
	 * In this implementation the method will not go over every possible pedestrian.
	 */
	boolean fasterSearch = true;




	public SIRGroupModel() {
		this.groupsById = new LinkedHashMap<>();
		this.sourceNextGroups = new HashMap<>();
	}

	@Override
	public void initialize(List<Attributes> attributesList, Domain domain,
	                       AttributesAgent attributesPedestrian, Random random) {
		this.attributesSIRG = Model.findAttributes(attributesList, AttributesSIRG.class);
		this.topography = domain.getTopography();
		this.random = random;
        this.totalInfected = 0;

	}

	@Override
	public void setPotentialFieldTarget(IPotentialFieldTarget potentialFieldTarget) {
		this.potentialFieldTarget = potentialFieldTarget;
		// update all existing groups
		for (SIRGroup group : groupsById.values()) {
			group.setPotentialFieldTarget(potentialFieldTarget);
		}
	}

	@Override
	public IPotentialFieldTarget getPotentialFieldTarget() {
		return potentialFieldTarget;
	}

	/**
	 * We have made the assumption that only the SIR group will be used, that is why we hardcoded 2 as the ID for Removed.
	 * @return
	 */
	private int getFreeGroupId() {
		if(this.random.nextDouble() < this.attributesSIRG.getInfectionRate()
        || this.totalInfected < this.attributesSIRG.getInfectionsAtStart()) {
			if(!getGroupsById().containsKey(SIRType.ID_INFECTED.ordinal()))
			{
				SIRGroup g = getNewGroup(SIRType.ID_INFECTED.ordinal(), Integer.MAX_VALUE/2);
				getGroupsById().put(SIRType.ID_INFECTED.ordinal(), g);
			}
            this.totalInfected += 1;
			return SIRType.ID_INFECTED.ordinal();
		}
		else{
			if(!getGroupsById().containsKey(SIRType.ID_SUSCEPTIBLE.ordinal()))
			{
				SIRGroup g = getNewGroup(SIRType.ID_SUSCEPTIBLE.ordinal(), Integer.MAX_VALUE/2);
				getGroupsById().put(SIRType.ID_SUSCEPTIBLE.ordinal(), g);
			}
			return SIRType.ID_SUSCEPTIBLE.ordinal();
		}
	}


	@Override
	public void registerGroupSizeDeterminator(int sourceId, GroupSizeDeterminator gsD) {
		sourceNextGroups.put(sourceId, new LinkedList<>());
	}

	@Override
	public int nextGroupForSource(int sourceId) {
		return Integer.MAX_VALUE/2;
	}

	@Override
	public SIRGroup getGroup(final Pedestrian pedestrian) {
		SIRGroup group = groupsById.get(pedestrian.getGroupIds().getFirst());
		assert group != null : "No group found for pedestrian";
		return group;
	}

	@Override
	protected void registerMember(final Pedestrian ped, final SIRGroup group) {
		groupsById.putIfAbsent(ped.getGroupIds().getFirst(), group);

		//logger.info("Pedestrian: " + ped.getId() + " is in group: " + ped.getGroupIds() + ". " + "SusceptibleID is: " + SIRType.ID_SUSCEPTIBLE.ordinal() + ". InfectedID is: " + SIRType.ID_INFECTED.ordinal() + ". RemovedID is: " + SIRType.ID_REMOVED.ordinal() + ".");

	}

	@Override
	public Map<Integer, SIRGroup> getGroupsById() {
		return groupsById;
	}

	@Override
	protected SIRGroup getNewGroup(final int size) {
		return getNewGroup(getFreeGroupId(), size);
	}

	@Override
	protected SIRGroup getNewGroup(final int id, final int size) {
		if(groupsById.containsKey(id))
		{
			return groupsById.get(id);
		}
		else
		{
			return new SIRGroup(id, this);
		}
	}

	private void initializeGroupsOfInitialPedestrians() {
		// get all pedestrians already in topography
		DynamicElementContainer<Pedestrian> c = topography.getPedestrianDynamicElements();

		if (c.getElements().size() > 0) {
			// Here you can fill in code to assign pedestrians in the scenario at the beginning (i.e., not created by a source)
            //  to INFECTED or SUSCEPTIBLE groups. This is not required in the exercise though.
		}
	}

	protected synchronized void assignToGroup(Pedestrian ped, int groupId) {
		SIRGroup currentGroup = getNewGroup(groupId, Integer.MAX_VALUE/2);
		currentGroup.addMember(ped);
		ped.getGroupIds().clear();
		ped.getGroupSizes().clear();
		ped.addGroupId(currentGroup.getID(), currentGroup.getSize());
		registerMember(ped, currentGroup);

		ped.group = groupId;
	}

	protected synchronized void assignToGroup(Pedestrian ped) {
		int groupId = getFreeGroupId();
		assignToGroup(ped, groupId);

		ped.group = groupId;
	}


	/* DynamicElement Listeners */

	@Override
	public void elementAdded(Pedestrian pedestrian) {
		assignToGroup(pedestrian);
	}

	@Override
	public void elementRemoved(Pedestrian pedestrian) {
		Group group = groupsById.get(pedestrian.getGroupIds().getFirst());
		if (group.removeMember(pedestrian)) { // if true pedestrian was last member.
			groupsById.remove(group.getID());
		}
	}

	/* Model Interface */

	@Override
	public void preLoop(final double simTimeInSec) {
		initializeGroupsOfInitialPedestrians();
		topography.addElementAddedListener(Pedestrian.class, this);
		topography.addElementRemovedListener(Pedestrian.class, this);
	}

	@Override
	public void postLoop(final double simTimeInSec) {
	}



	@Override
	public void update(final double simTimeInSec) {
		// check the positions of all pedestrians and switch groups to INFECTED (or REMOVED).
		DynamicElementContainer<Pedestrian> c = topography.getPedestrianDynamicElements();

		if (ourTimeModel) {
			//Check the current second
			double thisSec = (int) simTimeInSec;

			//If the current second is different from the previous one, it means that we can start again performing updates
			//in this second. Hence we reset the steps counter and we assign the current second to the previousSec variable.
			if (thisSec != previousSec) {
				stepsInThisSec = 0;
				previousSec = (int) thisSec;
			}

			//If we still find ourselves in the same second as in the previous step, we will perform an update
			//ONLY IF we have not reached the maximum amount of steps.
			if (stepsInThisSec < maxStepsPerSec) {
				stepsInThisSec++;
			}

			//If we reached the maximum number of steps, we will skip the update step, until we reached a new second.
			else {
				return;
			}
		}

		if (c.getElements().size() > 0) {
			for(Pedestrian p : c.getElements()) {
				// loop over neighbors and set infected if we are close

				//This is the start of the implementation where pedestrians can recover.
				if (includeRecovered == true) {
					//Get the group of the current pedestrian.
					SIRGroup g = getGroup(p);

					//If they are infected, they could recover.
					if (g.getID() == SIRType.ID_INFECTED.ordinal()) {
						//Sample the recovery rate and perform the following if the sampling is successful
						if (this.random.nextDouble() < attributesSIRG.getRecoveryRate()) {
							//If this is the first recovered person, we will need to firstly create the group
							if(!getGroupsById().containsKey(SIRType.ID_REMOVED.ordinal())) {
								SIRGroup g_new = getNewGroup(SIRType.ID_REMOVED.ordinal(), Integer.MAX_VALUE/2);
								getGroupsById().put(SIRType.ID_REMOVED.ordinal(), g_new);
							}

							//Remove the person from their previous group, i.e. the infected ones.
							elementRemoved(p);
							//Add them to the group of recovered persons.
							assignToGroup(p, SIRType.ID_REMOVED.ordinal());
							//This person cannot infect any other persons, so we proceed with the remaining persons.
							continue;
						}
					}
				}

				//This is the start of the implementation where the search for neighbours to infect is done more effectively.
				if (fasterSearch) {
					//Get the current position of the current pedestrian.
					VPoint pedestrian_position = p.getPosition();

					//Get the maximum distance possible for an infection to occur this is set in org.vadere.state.attributes.models->AttributesSIRG.java
					double infectionMaxDistance = attributesSIRG.getInfectionMaxDistance();

					//We create the linkedGrid based on the global topography and the class of the pedestrian, because we are only looking for such instances.
					//We studied LinkedCellsGrid objects in other implementation in this project and we have found the following usage:
					LinkedCellsGrid<Pedestrian> linkedGrid = topography.getSpatialMap(Pedestrian.class);

					//With the help of the getObjects function we can get the pedestrians at a max distance around the position of the current pedestrian.
					List<Pedestrian> neighbors = linkedGrid.getObjects(pedestrian_position, infectionMaxDistance);

					//During the debugging phase we have used the following lines to get data about the neighbourhoods.
					//logger.info("pedestrian_id: " + p.getId() + " | pedestrian_pos: " + pedestrian_position + " | neighborhood_size is: " + neighbors.size()+ " | neighbor_id is: " + neighbors.get(0).getId());

					//For every neighbour do the following (we do not have to check for distance anymore, since we know for sure that this neighbours find themselves
					//in the required range.
					for(Pedestrian p_neighbor : neighbors) {
						//If the same pedestrian is returned or the neighbour is not already infected do nothing.
						if(p == p_neighbor || getGroup(p_neighbor).getID() != SIRType.ID_INFECTED.ordinal())
							continue;

						//If the sample for the infection is successful, check if we have a neighbour that is infected and could infect the pedestrian.
						if (this.random.nextDouble() < attributesSIRG.getInfectionRate()) {
							//If the pedestrian is infected and the neighbour is infected, infect the current pedestrian as well.
							SIRGroup g = getGroup(p);
							if (g.getID() == SIRType.ID_SUSCEPTIBLE.ordinal()) {
								elementRemoved(p);
								assignToGroup(p, SIRType.ID_INFECTED.ordinal());
							}
						}
					}
				}

				//Original implementation for the neighbourhood search with quadratic efficiency in the number of pedestrians.
				else{
					for(Pedestrian p_neighbor : c.getElements()) {
						if(p == p_neighbor || getGroup(p_neighbor).getID() != SIRType.ID_INFECTED.ordinal())
							continue;
						double dist = p.getPosition().distance(p_neighbor.getPosition());
						if (dist < attributesSIRG.getInfectionMaxDistance() &&
								this.random.nextDouble() < attributesSIRG.getInfectionRate()) {
							SIRGroup g = getGroup(p);
							if (g.getID() == SIRType.ID_SUSCEPTIBLE.ordinal()) {
								elementRemoved(p);
								assignToGroup(p, SIRType.ID_INFECTED.ordinal());
							}
						}
					}
				}
			}
		}
	}
}